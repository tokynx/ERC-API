import json
import os
import logging
from web3 import Web3
from web3.exceptions import TransactionNotFound, BlockNotFound

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PolygonSDK:
    def __init__(self, provider_url: str):
        """
        Initialize the Polygon SDK with a provider URL (e.g., Infura or Alchemy).
        """
        self.provider_url = provider_url
        self.web3 = Web3(Web3.HTTPProvider(provider_url))

        if not self.web3.isConnected():
            raise ConnectionError("Failed to connect to Polygon provider.")
        logger.info(f"Connected to Polygon provider: {provider_url}")

    def get_block(self, block_number: int = 'latest'):
        """
        Get block details by block number.
        Default is the latest block.
        """
        try:
            return self.web3.eth.getBlock(block_number)
        except BlockNotFound:
            logger.error(f"Block not found: {block_number}")
            return None

    def get_transaction(self, tx_hash: str):
        """
        Get transaction details by transaction hash.
        """
        try:
            return self.web3.eth.getTransaction(tx_hash)
        except TransactionNotFound:
            logger.error(f"Transaction not found: {tx_hash}")
            return None

    def get_balance(self, address: str):
        """
        Get the balance of a Polygon address in Wei.
        """
        try:
            return self.web3.eth.getBalance(address)
        except ValueError as e:
            logger.error(f"Error getting balance for {address}: {e}")
            return None

    def send_transaction(self, private_key: str, to_address: str, amount_wei: int):
        """
        Send POL from one address to another on the Polygon network.
        """
        try:
            account = self.web3.eth.account.privateKeyToAccount(private_key)
            transaction = {
                'to': to_address,
                'value': amount_wei,
                'gas': 2000000,
                'gasPrice': self.web3.toWei('20', 'gwei'),
                'nonce': self.web3.eth.getTransactionCount(account.address),
            }

            # Sign the transaction
            signed_txn = self.web3.eth.account.signTransaction(transaction, private_key)
            tx_hash = self.web3.eth.sendRawTransaction(signed_txn.rawTransaction)

            logger.info(f"Transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except ValueError as e:
            logger.error(f"Transaction error: {e}")
            return None

    def call_contract_function(self, contract_address: str, abi: str, function_name: str, args: list = []):
        """
        Call a smart contract function on Polygon.
        """
        try:
            contract = self.web3.eth.contract(address=contract_address, abi=json.loads(abi))
            function = contract.get_function_by_name(function_name)(*args)
            return function.call()
        except Exception as e:
            logger.error(f"Error calling contract function {function_name}: {e}")
            return None

    def send_contract_transaction(self, private_key: str, contract_address: str, abi: str, function_name: str, args: list):
        """
        Send a transaction to invoke a smart contract function on Polygon.
        """
        try:
            contract = self.web3.eth.contract(address=contract_address, abi=json.loads(abi))
            function = contract.get_function_by_name(function_name)(*args)

            account = self.web3.eth.account.privateKeyToAccount(private_key)
            transaction = function.buildTransaction({
                'chainId': 137,  # Polygon Mainnet chain ID
                'gas': 2000000,
                'gasPrice': self.web3.toWei('20', 'gwei'),
                'nonce': self.web3.eth.getTransactionCount(account.address),
            })

            signed_txn = self.web3.eth.account.signTransaction(transaction, private_key)
            tx_hash = self.web3.eth.sendRawTransaction(signed_txn.rawTransaction)

            logger.info(f"Contract transaction sent: {tx_hash.hex()}")
            return tx_hash.hex()

        except Exception as e:
            logger.error(f"Error sending contract transaction: {e}")
            return None

    def get_erc20_balance(self, token_address: str, wallet_address: str):
        """
        Get ERC20 token balance on the Polygon network.
        """
        try:
            erc20_abi = json.dumps([{
                "constant": True,
                "inputs": [{"name": "owner", "type": "address"}],
                "name": "balanceOf",
                "outputs": [{"name": "", "type": "uint256"}],
                "payable": False,
                "stateMutability": "view",
                "type": "function"
            }])
            return self.call_contract_function(token_address, erc20_abi, "balanceOf", [wallet_address])

        except Exception as e:
            logger.error(f"Error getting ERC20 token balance: {e}")
            return None


# Example usage
if __name__ == '__main__':
    provider_url = os.getenv("POLYGON_PROVIDER_URL", "https://polygon-mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID")
    sdk = PolygonSDK(provider_url)

    # Example 1: Get block details
    block = sdk.get_block(12345678)
    if block:
        logger.info(f"Block: {block}")

    # Example 2: Get the balance of an address
    wallet_address = "0xYourWalletAddress"
    balance = sdk.get_balance(wallet_address)
    if balance is not None:
        logger.info(f"Balance: {sdk.web3.fromWei(balance, 'ether')} POL")

    # Example 3: Send POL
    private_key = os.getenv("PRIVATE_KEY")  # Never hardcode private keys in the code
    to_address = "0xRecipientAddress"
    amount_wei = sdk.web3.toWei(0.1, 'ether')  # 0.1 POL in Wei
    tx_hash = sdk.send_transaction(private_key, to_address, amount_wei)
    if tx_hash:
        logger.info(f"Transaction Hash: {tx_hash}")

    # Example 4: Interact with an ERC20 contract (Get Token Balance)
    token_address = "0xYourTokenAddress"
    token_balance = sdk.get_erc20_balance(token_address, wallet_address)
    if token_balance is not None:
        logger.info(f"ERC20 Token Balance: {token_balance}")
