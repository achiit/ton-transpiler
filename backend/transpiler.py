# backend/transpiler.py
import re
from typing import List, Dict, Optional, Union

class SolidityParser:
    def __init__(self):
        self.contract_name = ""
        self.is_interface = False
        self.state_variables: List[Dict[str, str]] = []
        self.functions: List[Dict] = []
        self.events: List[Dict] = []
        
    def parse_solidity(self, code: str) -> None:
        # Clean the code
        code = self._remove_comments(code)
        
        # Check if it's an interface or contract
        interface_match = re.search(r'interface\s+(\w+)', code)
        contract_match = re.search(r'contract\s+(\w+)', code)
        
        if interface_match:
            self.is_interface = True
            self.contract_name = interface_match.group(1)
            self._parse_interface_functions(code)
        elif contract_match:
            self.contract_name = contract_match.group(1)
            self._parse_contract(code)
            
    def _remove_comments(self, code: str) -> str:
        # Remove license and pragma
        code = re.sub(r'// SPDX-License-Identifier:.*?\n', '', code)
        code = re.sub(r'pragma solidity.*?\n', '', code)
        # Remove single-line comments
        code = re.sub(r'//.*?$', '', code, flags=re.MULTILINE)
        # Remove multi-line comments
        code = re.sub(r'/\*.*?\*/', '', code, flags=re.DOTALL)
        return code

    def _parse_interface_functions(self, code: str) -> None:
        # Parse interface functions
        function_pattern = r'function\s+(\w+)\s*\((.*?)\)\s*external\s*(?:(?:pure|view)\s+)?(?:returns\s*\((.*?)\))?\s*;'
        functions = re.findall(function_pattern, code)
        
        for name, params, returns in functions:
            self.functions.append({
                'name': name,
                'params': self._parse_params(params),
                'visibility': 'external',
                'returns': self._parse_returns(returns),
                'body': None,
                'modifiers': []
            })

    def _parse_contract(self, code: str) -> None:
        # Parse state variables
        state_var_pattern = r'([\w\[\]]+)\s+(?:private\s+|public\s+|internal\s+)?(\w+)\s*(?:=\s*([^;]+))?\s*;'
        state_vars = re.findall(state_var_pattern, code)
        
        self.state_variables = [
            {
                'type': var_type.strip(),
                'name': var_name.strip(),
                'initial_value': init_value.strip() if init_value else None
            }
            for var_type, var_name, init_value in state_vars
        ]

        # Parse functions with bodies
        function_pattern = r'function\s+(\w+)\s*\((.*?)\)\s*(public|private|external|internal)?\s*(?:(?:pure|view|payable)\s+)?(?:returns\s*\((.*?)\))?\s*{([^}]*?)}'
        functions = re.findall(function_pattern, code, re.DOTALL)
        
        for name, params, visibility, returns, body in functions:
            self.functions.append({
                'name': name,
                'params': self._parse_params(params),
                'visibility': visibility or 'public',
                'returns': self._parse_returns(returns),
                'body': body.strip(),
                'modifiers': self._extract_modifiers(body)
            })

    def _parse_params(self, params: str) -> List[Dict[str, str]]:
        if not params.strip():
            return []
            
        param_list = []
        for param in params.split(','):
            param = param.strip()
            if param:
                try:
                    param_parts = param.split()
                    param_type = ' '.join(param_parts[:-1])
                    param_name = param_parts[-1]
                    param_list.append({
                        'type': param_type.strip(),
                        'name': param_name.strip()
                    })
                except Exception as e:
                    print(f"Error parsing parameter: {param} - {str(e)}")
        return param_list

    def _parse_returns(self, returns: str) -> Optional[str]:
        if not returns:
            return None
        returns = returns.strip()
        if ' ' in returns:
            return returns.split()[-1]
        return returns

    def _extract_modifiers(self, body: str) -> List[str]:
        modifier_pattern = r'modifier\s+(\w+)'
        return re.findall(modifier_pattern, body)

class TactGenerator:
    TYPE_MAPPING = {
        'uint256': 'Int as uint256',
        'uint': 'Int as uint256',
        'int': 'Int',
        'bool': 'Bool',
        'address': 'Address',
        'string': 'String',
        'bytes': 'Cell',
        'uint8': 'Int as uint8',
        'uint128': 'Int as uint128'
    }
    
    def __init__(self, parser: SolidityParser):
        self.parser = parser
        
    def generate_tact(self) -> str:
        lines = []
        
        # Add standard imports
        lines.append('import "@stdlib/deploy";')
        lines.append('')
        
        if self.parser.is_interface:
            lines.extend(self._generate_interface())
        else:
            lines.extend(self._generate_contract())
            
        return '\n'.join(lines)
    
    def _generate_interface(self) -> List[str]:
        lines = []
        lines.append(f'trait {self.parser.contract_name} {{')
        
        # Generate interface functions
        for func in self.parser.functions:
            lines.extend(self._generate_interface_function(func))
            lines.append('')
            
        lines.append('}')
        return lines
    
    def _generate_contract(self) -> List[str]:
        lines = []
        
        # Generate message types for functions with parameters
        for func in self.parser.functions:
            if func['params']:
                lines.extend(self._generate_message_type(func))
                lines.append('')
        
        # Start contract definition
        lines.append(f'contract {self.parser.contract_name} with Deployable {{')
        
        # Generate state variables
        for var in self.parser.state_variables:
            initial_value = f' = {var["initial_value"]}' if var["initial_value"] else ''
            lines.append(f'    {var["name"]}: {self._convert_type(var["type"])}{initial_value};')
        
        # Generate init function
        lines.extend(self._generate_init())
        
        # Generate contract functions
        for func in self.parser.functions:
            lines.extend(self._generate_contract_function(func))
            
        lines.append('}')
        return lines
    
    def _convert_type(self, solidity_type: str) -> str:
        base_type = solidity_type.replace('[]', '').strip()
        tact_type = self.TYPE_MAPPING.get(base_type, base_type)
        if '[]' in solidity_type:
            return f'map<Int, {tact_type}>'
        return tact_type
    
    def _generate_message_type(self, func: Dict) -> List[str]:
        if not func['params']:
            return []
            
        lines = []
        message_name = f'{func["name"].capitalize()}'
        lines.append(f'message {message_name} {{')
        
        for param in func['params']:
            lines.append(f'    {param["name"]}: {self._convert_type(param["type"])};')
            
        lines.append('}')
        return lines

    def _generate_interface_function(self, func: Dict) -> List[str]:
        params_str = ', '.join([f'{p["name"]}: {self._convert_type(p["type"])}' 
                              for p in func['params']])
        return_type = self._convert_type(func['returns']) if func['returns'] else 'Bool'
        
        return [f'    fun {func["name"]}({params_str}): {return_type};']

    def _generate_init(self) -> List[str]:
        lines = ['\n    init() {']
        
        # Initialize state variables
        for var in self.parser.state_variables:
            if not var.get('initial_value'):
                var_type = var['type']
                if var_type in ['uint256', 'uint', 'int', 'uint8', 'uint128']:
                    lines.append(f'        self.{var["name"]} = 0;')
                elif var_type == 'bool':
                    lines.append(f'        self.{var["name"]} = false;')
                elif var_type == 'address':
                    lines.append(f'        self.{var["name"]} = newAddress(0);')
                elif '[]' in var_type:
                    lines.append(f'        self.{var["name"]} = new Map();')
                    
        lines.append('    }')
        return lines

    def _generate_contract_function(self, func: Dict) -> List[str]:
        lines = ['\n']
        
        if func['params']:
            # Generate receive function for message
            lines.append(f'    receive(msg: {func["name"].capitalize()}) {{')
            if func['body']:
                body = self._convert_function_body(func['body'], func['params'])
                lines.extend([f'        {line}' for line in body.split('\n')])
            lines.append('    }')
        else:
            # Generate get function
            return_type = self._convert_type(func['returns']) if func['returns'] else 'Int'
            lines.append(f'    get fun {func["name"]}(): {return_type} {{')
            if func['body']:
                body = self._convert_function_body(func['body'], [])
                lines.extend([f'        {line}' for line in body.split('\n')])
            else:
                lines.append('        return 0; // Implementation needed')
            lines.append('    }')
            
        return lines

    def _convert_function_body(self, body: str, params: List[Dict]) -> str:
        if not body:
            return 'return 0;'
            
        body = body.strip()
        
        # Convert require statements
        body = re.sub(r'require\((.*?)\);', r'require(\1);', body)
        
        # Convert msg.sender
        body = body.replace('msg.sender', 'sender()')
        
        # Convert state variable access
        for var in self.parser.state_variables:
            body = re.sub(f'\\b{var["name"]}\\b', f'self.{var["name"]}', body)
        
        # Convert parameter access
        for param in params:
            body = re.sub(f'\\b{param["name"]}\\b', f'msg.{param["name"]}', body)
            
        return body

def transpile_solidity_to_tact(solidity_code: str) -> str:
    parser = SolidityParser()
    parser.parse_solidity(solidity_code)
    
    generator = TactGenerator(parser)
    return generator.generate_tact()