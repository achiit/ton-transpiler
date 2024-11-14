// // sources/contract.deploy.ts
// import { beginCell, contractAddress, toNano } from "ton";
// import { testAddress } from "ton-emulator";
// import { SimpleStorage } from "../build/sample_SimpleStorage"; // This will be generated
// import { deploy } from "./utils/deploy";
// import { printAddress, printDeploy, printHeader } from "./utils/print";

// (async () => {
//     Parameters
//     let init = await SimpleStorage.init();
//     let address = contractAddress(0, init);
//     let deployAmount = toNano('0.1');
//     let testnet = true;

//     // Print basics
//     printHeader('SimpleStorage');
//     printAddress(address);
    
//     // Do deploy
//     await deploy(init, deployAmount, "Deploy SimpleStorage", testnet);
// })();