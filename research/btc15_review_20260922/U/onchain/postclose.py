"""Two preselected post-close anomalies; --fetch makes at most four public reads."""
from decimal import Decimal as D
from datetime import datetime
import sys
import probe as p


def main():
    selected = p.read(p.OUT/'postclose_selection.json')
    assert selected['total_unique_transactions'] <= selected['max_unique_transactions']
    findings = []
    for row in selected['rows']:
        path = p.OUT/'raw'/f"postclose_receipt_{row['tx']}.json"
        if '--fetch' in sys.argv:
            p.request(p.RPCS[0], 'eth_getTransactionReceipt', [row['tx']], path)
        receipt = p.read(path)['response']['result']
        assert receipt['transactionHash'] == row['tx'] and receipt['status'] == '0x1'
        block_path = p.OUT/'raw'/f"postclose_block_{receipt['blockNumber']}.json"
        if '--fetch' in sys.argv:
            p.request(p.RPCS[0], 'eth_getBlockByNumber', [receipt['blockNumber'], False], block_path)
        block = p.read(block_path)['response']['result']
        assert block['hash'] == receipt['blockHash']
        block_ts = int(block['timestamp'], 16)
        market = p.read(p.OUT/f"postclose_{row['slug']}.json")
        official_end = int(datetime.fromisoformat(market['endDate'].replace('Z', '+00:00')).timestamp())
        assert official_end == row['S']+900, 'official contract duration mismatch'
        tokens = p.json.loads(market['clobTokenIds'])
        decoded = p.dec.decode(receipt, p.ACTOR)
        assert all(f['token'] == tokens[row['side']] and f['side'] == 0 for f in decoded)
        assert abs(sum(D(f['qty']) for f in decoded)/p.UNIT-D(row['qty'])) <= D('.000001')
        assert abs(sum(D(f['cash_cost']) for f in decoded)/p.UNIT-D(row['cash'])) <= D('.00001')
        findings.append(dict(slug=row['slug'], transaction=row['tx'], official_end=market['endDate'],
            api_ts=row['ts'], block_ts=block_ts, block_hash=block['hash'], block_number=int(block['number'],16),
            api_minus_block_seconds=row['ts']-block_ts, seconds_after_close=block_ts-official_end,
            api_qty=row['qty'], api_cash=row['cash'], decoded=decoded,
            condition_id=market['conditionId'], token_identity_and_transfers_verified=True))
    result = dict(status='VERIFIED_SETTLEMENT_TIMESTAMP_NOT_DECISION_TIME', findings=findings,
        limitation='The block timestamp proves post-close settlement; neither submission nor off-chain match time is observed.')
    p.save(p.OUT/'postclose_results.json', result)
    print(p.json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
