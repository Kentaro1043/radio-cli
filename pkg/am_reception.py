import threading

import osmosdr
from gnuradio import analog, audio, filter, gr
from gnuradio.fft import window
from gnuradio.filter import firdes


class am_reception(gr.top_block):
    def __init__(self, device_args="hackrf=0", freqency=954e3, rf_gain=20):
        gr.top_block.__init__(
            self,
            "AM Reception",
            catch_exceptions=True,
        )
        self.flowgraph_started = threading.Event()

        self.freqency = freqency
        self.samp_rate = samp_rate = 32000
        self.center_freq = center_freq = 2e6

        self.osmosdr_source = osmosdr.source(
            args="numchan=" + str(1) + " " + device_args
        )
        self.osmosdr_source.set_sample_rate((samp_rate * 100))
        self.osmosdr_source.set_center_freq(center_freq, 0)
        self.osmosdr_source.set_freq_corr(0, 0)
        self.osmosdr_source.set_dc_offset_mode(2, 0)
        self.osmosdr_source.set_iq_balance_mode(0, 0)
        self.osmosdr_source.set_gain_mode(True, 0)
        self.osmosdr_source.set_gain(rf_gain, 0)
        self.osmosdr_source.set_if_gain(20, 0)
        self.osmosdr_source.set_bb_gain(20, 0)
        self.osmosdr_source.set_antenna("", 0)
        self.osmosdr_source.set_bandwidth(0, 0)
        self.low_pass_filter = filter.fir_filter_ccf(
            100,
            firdes.low_pass(1, (samp_rate * 100), 8e3, 2e3, window.WIN_HAMMING, 6.76),
        )
        self.freq_xlating_fir_filter_xxx = filter.freq_xlating_fir_filter_ccc(
            1, [32], (freqency - center_freq), (samp_rate * 100)
        )
        self.audio_sink_0 = audio.sink(samp_rate, "", True)
        self.analog_am_demod_cf = analog.am_demod_cf(
            channel_rate=samp_rate,
            audio_decim=1,
            audio_pass=5000,
            audio_stop=6000,
        )

        self.connect((self.analog_am_demod_cf, 0), (self.audio_sink_0, 0))
        self.connect((self.freq_xlating_fir_filter_xxx, 0), (self.low_pass_filter, 0))
        self.connect((self.low_pass_filter, 0), (self.analog_am_demod_cf, 0))
        self.connect((self.osmosdr_source, 0), (self.freq_xlating_fir_filter_xxx, 0))

    def get_tune(self):
        return self.tune

    def set_tune(self, tune):
        self.tune = tune
        self.freq_xlating_fir_filter_xxx.set_center_freq((self.tune - self.center_freq))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.low_pass_filter.set_taps(
            firdes.low_pass(
                1, (self.samp_rate * 100), 8e3, 2e3, window.WIN_HAMMING, 6.76
            )
        )
        self.osmosdr_source.set_sample_rate((self.samp_rate * 100))

    def get_center_freq(self):
        return self.center_freq

    def set_center_freq(self, center_freq):
        self.center_freq = center_freq
        self.freq_xlating_fir_filter_xxx.set_center_freq((self.tune - self.center_freq))
        self.osmosdr_source.set_center_freq(self.center_freq, 0)
