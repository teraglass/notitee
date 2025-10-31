from module.dollar_currency import dollar_currency_analysis
from module.cnn_fear_greed import cnn_fear_greed_main
from module.snp500_200ma import snp500_200ma_main

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    dollar_currency_analysis()
    cnn_fear_greed_main()
    snp500_200ma_main()

if __name__ == "__main__":
    main()