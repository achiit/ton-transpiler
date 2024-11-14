import "@stdlib/deploy";

trait IERC20 {
    fun totalSupply(): Int as uint256;

    fun balanceOf(account: Address): Int as uint256;

    fun transfer(recipient: Address, amount: Int as uint256): Bool;

    fun allowance(owner: Address, spender: Address): Int as uint256;

    fun approve(spender: Address, amount: Int as uint256): Bool;

    fun transferFrom(sender: Address, recipient: Address, amount: Int as uint256): Bool;

}