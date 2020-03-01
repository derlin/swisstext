# SwissText

A suite of automated tools for the creation of Swiss German corpora by semi-automated web crawling.


<p align=center> ✻ Read the docs https://derlin.github.io/swisstext ✻ </p>
<p align=center> ✻ Overview (Google Slides) http://bit.ly/swisstext-slides ✻ </p>

-------------------------------------------------

**Paper**: (LREC, 2020) \
[Automatic Creation of Text Corpora for Low-Resource Languages from the Internet: The Case of Swiss German](https://arxiv.org/abs/1912.00159)

**Citation**:
```bibtex
@article{linder2019automatic,
  title={Automatic Creation of Text Corpora for Low-Resource Languages from the Internet: The Case of Swiss German},
  author={Linder, Lucy and Jungo, Michael and Hennebert, Jean and Musat, Claudiu and Fischer, Andreas},
  journal={arXiv preprint arXiv:1912.00159},
  year={2019}
}
```
→ See the **branch [lrec](https://github.com/derlin/swisstext/tree/lrec)** and 
the **repository [swisstext-lrec](https://github.com/derlin/swisstext-lrec)** for the exact version used in the paper.

-------------------------------------------------

## Installation and usage

Install the tools:
```bash
# clone
git clone git@github.com:derlin/swisstext.git
# install (note: pass the option -d for editable mode)
./install.sh
```
This will make the following commands available:

* `st_search`: make queries to a search engine and retrieve potentially interesting URLs;
* `st_scrape`: visit URLs in order to find new sentences;
* `st_frontend`: launch a webapp to manage the database, validate and label sentences, propose new seeds and much more.

Find more in the [documentation](https://derlin.github.io/swisstext) or the [overview slides](http://bit.ly/swisstext-slides).


-------------------------------------------------

SwissText Crawler (c) by Lucy Linder

The SwissText Crawler is licensed under a Creative Commons Attribution-NonCommercial 4.0 Unported License.

You should have received a copy of the license along with this work.  
If not, see <http://creativecommons.org/licenses/by-nc/4.0/>.
