#
# requires mclid from Matthias Christe
#

class EnsembleDetector:

    def __init__(self, pmc=0.90, pll=0.85, return_proba='mc'):
        from swisstext.mclid import TfLangidGsw
        from swisstext.cmd.scraping.tools import SwigspotLangid
        self.pmc, self.pll = pmc, pll
        self._mc = TfLangidGsw()
        self._ll = SwigspotLangid()
        if return_proba == 'll':
            self._choose = lambda pm, pl: pl
        else:
            self._choose = lambda pm, pl: pm

    def predict(self, sentences):

        return [
            self._choose(pm, pl)
            if pm >= self.pmc and pl >= self.pll else .0
            for pm, pl
            in zip(self._mc.predict(sentences), self._ll.predict(sentences))
        ]
