import argparse
import signal
import sys
import threading

import osmosdr
from gnuradio import analog, audio, filter, gr
from gnuradio.fft import window
from gnuradio.filter import firdes


class fm_reception(gr.top_block):
    def __init__(self, frequency=82.5e6, device_args="hackrf=0", rf_gain=20):
        gr.top_block.__init__(self, "FM Reception", catch_exceptions=True)
        self.flowgraph_started = threading.Event()

        self.samp_rate = samp_rate = 48000
        self.frequency = frequency

        self.rtlsdr_source_0 = osmosdr.source(
            args="numchan=" + str(1) + " " + device_args
        )
        self.rtlsdr_source_0.set_time_unknown_pps(osmosdr.time_spec_t())
        self.rtlsdr_source_0.set_sample_rate((samp_rate * 50))
        self.rtlsdr_source_0.set_center_freq(frequency, 0)
        self.rtlsdr_source_0.set_freq_corr(0, 0)
        self.rtlsdr_source_0.set_dc_offset_mode(0, 0)
        self.rtlsdr_source_0.set_iq_balance_mode(0, 0)
        self.rtlsdr_source_0.set_gain_mode(False, 0)
        self.rtlsdr_source_0.set_gain(rf_gain, 0)
        self.rtlsdr_source_0.set_if_gain(20, 0)
        self.rtlsdr_source_0.set_bb_gain(20, 0)
        self.rtlsdr_source_0.set_antenna("", 0)
        self.rtlsdr_source_0.set_bandwidth(0, 0)
        self.low_pass_filter_0 = filter.fir_filter_ccf(
            5,
            firdes.low_pass(1, (samp_rate * 50), 300e3, 50e3, window.WIN_HAMMING, 6.76),
        )
        self.audio_sink_0 = audio.sink(samp_rate, "", True)
        self.analog_wfm_rcv_0 = analog.wfm_rcv(
            quad_rate=(samp_rate * 10),
            audio_decimation=10,
        )

        self.connect((self.analog_wfm_rcv_0, 0), (self.audio_sink_0, 0))
        self.connect((self.low_pass_filter_0, 0), (self.analog_wfm_rcv_0, 0))
        self.connect((self.rtlsdr_source_0, 0), (self.low_pass_filter_0, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.low_pass_filter_0.set_taps(
            firdes.low_pass(
                1, (self.samp_rate * 50), 300e3, 50e3, window.WIN_HAMMING, 6.76
            )
        )
        self.rtlsdr_source_0.set_sample_rate((self.samp_rate * 50))

    def get_frequency(self):
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency
        self.rtlsdr_source_0.set_center_freq(self.frequency, 0)


def main():
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="ラジオ受信プログラム")
    parser.add_argument(
        "freqency",
        type=float,
        default=82.5,
        help="受信する周波数（MHz単位, 例: 82.5）。",
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
    frequency_hz = args.freqency * 1e6

    # 変調方式に応じた受信モジュールの初期化
    if args.type not in ["fm", "am"]:
        print("エラー: 変調方式は'fm'または'am'で指定してください。")
        sys.exit(1)
    elif args.type == "am":
        print("エラー: AM変調は現在サポートされていません。")
        sys.exit(1)
    else:
        print(f"FM変調で{args.freqency}MHzを受信します。")
        demodulator = fm_reception(frequency=frequency_hz)

    demodulator.set_frequency(frequency_hz)

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
