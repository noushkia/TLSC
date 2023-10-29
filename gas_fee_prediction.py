"""
This file contains code used for calculating the base gas fee for a range of blocks.
"""

MAX_INCREASE_RATE = 12.5
BLOCK_SIZE_LIMIT = 30_000_000
ETH_TO_GWEI = 1e9


def calculate_fee(curr_base_fee: float, _block_range: int, max_priority_fee_ratio: float = 0) -> float:
    _total_fee = 0
    for i in range(_block_range):
        curr_base_fee *= (1 + MAX_INCREASE_RATE / 100)
        _total_fee += curr_base_fee * (1 + max_priority_fee_ratio)
        if i in [1, 10, 50]:
            print(f"{i} blocks: {_total_fee}")
            print(f"cost for full block utilization: {_total_fee * BLOCK_SIZE_LIMIT / ETH_TO_GWEI} ETH")
    return _total_fee


if __name__ == "__main__":
    initial_base_fee = 20
    block_range = 100
    total_fee = calculate_fee(20, 100)
    print("Base fees for different block ranges:")
    print(f"{block_range} blocks: {total_fee}")
    print(f"cost for full block utilization: {total_fee * BLOCK_SIZE_LIMIT / ETH_TO_GWEI} ETH")

    total_fee = calculate_fee(20, 100, 0.05)  # 5% max fee
    print("Total fees for different block ranges:")
    print(f"{block_range} blocks: {total_fee}")
    print(f"cost for full block utilization: {total_fee * BLOCK_SIZE_LIMIT / ETH_TO_GWEI} ETH")
