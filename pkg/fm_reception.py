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

        self.rtlsdr_source = osmosdr.source(
            args="numchan=" + str(1) + " " + device_args
        )
        self.rtlsdr_source.set_time_unknown_pps(osmosdr.time_spec_t())
        self.rtlsdr_source.set_sample_rate((samp_rate * 50))
        self.rtlsdr_source.set_center_freq(frequency, 0)
        self.rtlsdr_source.set_freq_corr(0, 0)
        self.rtlsdr_source.set_dc_offset_mode(0, 0)
        self.rtlsdr_source.set_iq_balance_mode(0, 0)
        self.rtlsdr_source.set_gain_mode(False, 0)
        self.rtlsdr_source.set_gain(rf_gain, 0)
        self.rtlsdr_source.set_if_gain(20, 0)
        self.rtlsdr_source.set_bb_gain(20, 0)
        self.rtlsdr_source.set_antenna("", 0)
        self.rtlsdr_source.set_bandwidth(0, 0)
        self.low_pass_filter = filter.fir_filter_ccf(
            5,
            firdes.low_pass(1, (samp_rate * 50), 300e3, 50e3, window.WIN_HAMMING, 6.76),
        )
        self.audio_sink = audio.sink(samp_rate, "", True)
        self.analog_wfm_rcv = analog.wfm_rcv(
            quad_rate=(samp_rate * 10),
            audio_decimation=10,
        )

        self.connect((self.analog_wfm_rcv, 0), (self.audio_sink, 0))
        self.connect((self.low_pass_filter, 0), (self.analog_wfm_rcv, 0))
        self.connect((self.rtlsdr_source, 0), (self.low_pass_filter, 0))

    def get_samp_rate(self):
        return self.samp_rate

    def set_samp_rate(self, samp_rate):
        self.samp_rate = samp_rate
        self.low_pass_filter.set_taps(
            firdes.low_pass(
                1, (self.samp_rate * 50), 300e3, 50e3, window.WIN_HAMMING, 6.76
            )
        )
        self.rtlsdr_source.set_sample_rate((self.samp_rate * 50))

    def get_frequency(self):
        return self.frequency

    def set_frequency(self, frequency):
        self.frequency = frequency
        self.rtlsdr_source.set_center_freq(self.frequency, 0)
