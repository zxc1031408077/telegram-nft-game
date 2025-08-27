from web3 import Web3
import json
import os
import logging
from typing import Optional

from app.utils.helpers import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

class NFTManager:
    def __init__(self, network: str = None, contract_address: str = None, private_key: str = None):
        self.network = network or settings.blockchain_network
        self.contract_address = contract_address or settings.nft_contract_address
        self.private_key = private_key or settings.wallet_private_key
        
        # 根據網絡設置 Web3 提供商
        if self.network == "polygon":
            rpc_url = settings.polygon_rpc_url or "https://polygon-rpc.com"
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        elif self.network == "ethereum":
            rpc_url = settings.ethereum_rpc_url or "https://mainnet.infura.io/v3/YOUR-PROJECT-ID"
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        elif self.network == "bsc":
            rpc_url = settings.bsc_rpc_url or "https://bsc-dataseed.binance.org"
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        else:
            raise ValueError(f"Unsupported network: {self.network}")
        
        # 檢查連接
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {self.network} network")
        
        # 載入合約 ABI
        try:
            with open('app/nft/contract_abi.json', 'r') as abi_file:
                self.contract_abi = json.load(abi_file)
        except FileNotFoundError:
            logger.warning("Contract ABI file not found, using empty ABI")
            self.contract_abi = []
        
        if self.contract_address:
            self.contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(self.contract_address),
                abi=self.contract_abi
            )
        else:
            self.contract = None
        
        if self.private_key:
            self.account = self.w3.eth.account.from_key(self.private_key)
        else:
            self.account = None
            logger.warning("No private key provided, NFT minting will be disabled")
    
    def mint_nft(self, to_address: str, token_uri: str, metadata: dict) -> Optional[str]:
        """鑄造 NFT"""
        if not self.contract or not self.account:
            logger.error("NFT contract or account not initialized")
            return None
        
        try:
            # 構建交易
            nonce = self.w3.eth.get_transaction_count(self.account.address)
            
            transaction = self.contract.functions.mintNFT(
                Web3.to_checksum_address(to_address), token_uri
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 200000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
            })
            
            # 簽名交易
            signed_txn = self.w3.eth.account.sign_transaction(transaction, private_key=self.private_key)
            
            # 發送交易
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
            
            # 等待交易確認
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if receipt.status == 1:
                # 從事件日志中提取 tokenId
                transfer_event = self.contract.events.Transfer().process_receipt(receipt)
                token_id = transfer_event[0]['args']['tokenId'] if transfer_event else None
                logger.info(f"NFT minted successfully: {token_id}")
                return str(token_id)
            else:
                logger.error(f"NFT minting failed: transaction reverted")
                return None
                
        except Exception as e:
            logger.error(f"Error minting NFT: {e}")
            return None
    
    def get_nft_owner(self, token_id: int) -> Optional[str]:
        """查詢 NFT 所有者"""
        if not self.contract:
            logger.error("NFT contract not initialized")
            return None
        
        try:
            return self.contract.functions.ownerOf(token_id).call()
        except Exception as e:
            logger.error(f"Error getting NFT owner: {e}")
            return None
    
    def get_nft_uri(self, token_id: int) -> Optional[str]:
        """查詢 NFT URI"""
        if not self.contract:
            logger.error("NFT contract not initialized")
            return None
        
        try:
            return self.contract.functions.tokenURI(token_id).call()
        except Exception as e:
            logger.error(f"Error getting NFT URI: {e}")
            return None