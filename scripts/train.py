"""Uso: python -m scripts.train --config configs/lora_a.json."""
import argparse
from src.training.pipeline import train

def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--config', required=True)
    args = parser.parse_args()
    train(args.config)

if __name__ == '__main__':
    main()
