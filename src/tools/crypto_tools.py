import json
import requests
from .base import BaseTool, ToolResult, EntityFound


class BlockchainBtcTool(BaseTool):
    name = "blockchain_btc"
    description = "Bitcoin address - balance, transactions, connected wallets"
    input_types = ["crypto_btc"]
    output_types = ["crypto_btc"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "crypto_btc":
            return self.make_result(selector, selector_type, "", [], False, "BTC tool only accepts Bitcoin addresses")

        try:
            resp = requests.get(
                f"https://blockchain.info/rawaddr/{selector}?limit=10",
                timeout=15,
            )
            raw_output = resp.text[:5000]
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                balance_btc = data.get("final_balance", 0) / 1e8
                n_tx = data.get("n_tx", 0)
                total_received = data.get("total_received", 0) / 1e8

                entities.append(EntityFound(
                    value=selector,
                    entity_type="crypto_btc",
                    confidence="confirmed",
                    source_citation=f"Balance: {balance_btc} BTC, Transactions: {n_tx}, Total Received: {total_received} BTC",
                    metadata={
                        "balance_btc": balance_btc,
                        "n_tx": n_tx,
                        "total_received_btc": total_received,
                        "total_sent_btc": data.get("total_sent", 0) / 1e8,
                    },
                ))

                seen_addresses = set()
                for tx in data.get("txs", [])[:10]:
                    for inp in tx.get("inputs", []):
                        prev = inp.get("prev_out", {})
                        addr = prev.get("addr")
                        if addr and addr != selector and addr not in seen_addresses:
                            seen_addresses.add(addr)
                            entities.append(EntityFound(
                                value=addr,
                                entity_type="crypto_btc",
                                confidence="confirmed",
                                source_citation=f"TX {tx.get('hash', '')[:16]}... input from {addr}",
                                metadata={"tx_hash": tx.get("hash", ""), "direction": "input"},
                            ))

                    for out in tx.get("out", []):
                        addr = out.get("addr")
                        if addr and addr != selector and addr not in seen_addresses:
                            seen_addresses.add(addr)
                            entities.append(EntityFound(
                                value=addr,
                                entity_type="crypto_btc",
                                confidence="confirmed",
                                source_citation=f"TX {tx.get('hash', '')[:16]}... output to {addr}",
                                metadata={"tx_hash": tx.get("hash", ""), "direction": "output"},
                            ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


class EtherscanTool(BaseTool):
    name = "etherscan"
    description = "Ethereum address transactions"
    input_types = ["crypto_eth"]
    output_types = ["crypto_eth"]
    method = "api"

    def query(self, selector: str, selector_type: str) -> ToolResult:
        if selector_type != "crypto_eth":
            return self.make_result(selector, selector_type, "", [], False, "Etherscan only accepts ETH addresses")

        try:
            resp = requests.get(
                f"https://api.etherscan.io/api?module=account&action=txlist&address={selector}&startblock=0&endblock=99999999&sort=desc&page=1&offset=10",
                timeout=15,
            )
            raw_output = resp.text[:5000]
            entities = []

            if resp.status_code == 200:
                data = resp.json()
                if data.get("status") == "1":
                    seen = set()
                    for tx in data.get("result", [])[:10]:
                        for addr_key in ("from", "to"):
                            addr = tx.get(addr_key, "")
                            if addr and addr.lower() != selector.lower() and addr not in seen:
                                seen.add(addr)
                                entities.append(EntityFound(
                                    value=addr,
                                    entity_type="crypto_eth",
                                    confidence="confirmed",
                                    source_citation=f"TX {tx.get('hash', '')[:16]}... {addr_key}: {addr}",
                                    metadata={
                                        "tx_hash": tx.get("hash", ""),
                                        "direction": addr_key,
                                        "value_wei": tx.get("value", "0"),
                                    },
                                ))

            return self.make_result(
                selector, selector_type, raw_output, entities,
                success=resp.status_code == 200,
            )
        except requests.RequestException as e:
            return self.make_result(selector, selector_type, "", [], False, str(e))


TOOLS = [BlockchainBtcTool(), EtherscanTool()]
