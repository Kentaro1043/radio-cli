import argparse
import signal
import sys

from pkg.am_reception import am_reception
from pkg.fm_reception import fm_reception


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="ラジオ受信プログラム")
    parser.add_argument(
        "freqency",
        type=float,
        help="受信する周波数（MHzまたはkHz）。FMの場合はMHz、AMの場合はkHzで指定してください。",
    )
    parser.add_argument(
        "--type",
        "-t",
        type=str,
        default="fm",
        help="変調方式（'fm'または'am'）。省略時は'fm'。",
    )
    parser.add_argument(
        "--device",
        "-d",
        type=str,
        default="hackrf=0",
        help="使用するSDRデバイスの引数。省略時は'hackrf=0'。",
    )
    parser.add_argument(
        "--gain",
        "-g",
        type=int,
        default=20,
        help="RFゲインの設定値。省略時は20。",
    )
    args = parser.parse_args()
    if args.type == "fm":
        frequency_hz = args.freqency * 1e6  # MHzをHzに変換
    else:
        frequency_hz = args.freqency * 1e3  # kHzをHzに変換

    # 変調方式に応じた受信モジュールの初期化
    if args.type not in ["fm", "am"]:
        print("エラー: 変調方式は'fm'または'am'で指定してください。")
        sys.exit(1)
    elif args.type == "am":
        print(f"AM変調で{args.freqency}kHzを受信します。")
        demodulator = am_reception(
            device_args=args.device, freqency=frequency_hz, rf_gain=args.gain
        )
    else:
        print(f"FM変調で{args.freqency}MHzを受信します。")
        demodulator = fm_reception(
            frequency=frequency_hz, device_args=args.device, rf_gain=args.gain
        )

    def sig_handler(sig=None, frame=None):
        demodulator.stop()
        demodulator.wait()

        sys.exit(0)

    signal.signal(signal.SIGINT, sig_handler)
    signal.signal(signal.SIGTERM, sig_handler)

    demodulator.start()
    demodulator.flowgraph_started.set()

    demodulator.wait()


if __name__ == "__main__":
    main()
