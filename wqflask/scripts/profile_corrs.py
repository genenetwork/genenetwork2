import io
import sys
import pstats
import cProfile

from flask import g, request

from wqflask import app
from wqflask.user_session import UserSession
from wqflask.correlation.correlation_gn3_api import compute_correlation

def sample_vals():
    return '{"C57BL/6J":"10.835","DBA/2J":"11.142","B6D2F1":"11.126","D2B6F1":"11.143","BXD1":"10.811","BXD2":"11.503","BXD5":"10.766","BXD6":"10.986","BXD8":"11.050","BXD9":"10.822","BXD11":"10.670","BXD12":"10.946","BXD13":"10.890","BXD14":"x","BXD15":"10.884","BXD16":"11.222","BXD18":"x","BXD19":"10.968","BXD20":"10.962","BXD21":"10.906","BXD22":"11.080","BXD23":"11.046","BXD24":"11.146","BXD24a":"x","BXD25":"x","BXD27":"11.078","BXD28":"11.034","BXD29":"10.808","BXD30":"x","BXD31":"11.087","BXD32":"11.029","BXD33":"10.662","BXD34":"11.482","BXD35":"x","BXD36":"x","BXD37":"x","BXD38":"10.836","BXD39":"10.926","BXD40":"10.638","BXD41":"x","BXD42":"10.974","BXD43":"10.828","BXD44":"10.900","BXD45":"11.358","BXD48":"11.042","BXD48a":"10.975","BXD49":"x","BXD50":"11.228","BXD51":"11.126","BXD52":"x","BXD53":"x","BXD54":"x","BXD55":"11.580","BXD56":"x","BXD59":"x","BXD60":"10.829","BXD61":"11.152","BXD62":"11.156","BXD63":"10.942","BXD64":"10.506","BXD65":"11.126","BXD65a":"11.272","BXD65b":"11.157","BXD66":"11.071","BXD67":"11.080","BXD68":"10.997","BXD69":"11.096","BXD70":"11.152","BXD71":"x","BXD72":"x","BXD73":"11.262","BXD73a":"11.444","BXD73b":"x","BXD74":"10.974","BXD75":"11.150","BXD76":"10.920","BXD77":"10.928","BXD78":"x","BXD79":"11.371","BXD81":"x","BXD83":"10.946","BXD84":"11.181","BXD85":"10.992","BXD86":"10.770","BXD87":"11.200","BXD88":"x","BXD89":"10.930","BXD90":"11.183","BXD91":"x","BXD93":"11.056","BXD94":"10.737","BXD95":"x","BXD98":"10.986","BXD99":"10.892","BXD100":"x","BXD101":"x","BXD102":"x","BXD104":"x","BXD105":"x","BXD106":"x","BXD107":"x","BXD108":"x","BXD109":"x","BXD110":"x","BXD111":"x","BXD112":"x","BXD113":"x","BXD114":"x","BXD115":"x","BXD116":"x","BXD117":"x","BXD119":"x","BXD120":"x","BXD121":"x","BXD122":"x","BXD123":"x","BXD124":"x","BXD125":"x","BXD126":"x","BXD127":"x","BXD128":"x","BXD128a":"x","BXD130":"x","BXD131":"x","BXD132":"x","BXD133":"x","BXD134":"x","BXD135":"x","BXD136":"x","BXD137":"x","BXD138":"x","BXD139":"x","BXD141":"x","BXD142":"x","BXD144":"x","BXD145":"x","BXD146":"x","BXD147":"x","BXD148":"x","BXD149":"x","BXD150":"x","BXD151":"x","BXD152":"x","BXD153":"x","BXD154":"x","BXD155":"x","BXD156":"x","BXD157":"x","BXD160":"x","BXD161":"x","BXD162":"x","BXD165":"x","BXD168":"x","BXD169":"x","BXD170":"x","BXD171":"x","BXD172":"x","BXD173":"x","BXD174":"x","BXD175":"x","BXD176":"x","BXD177":"x","BXD178":"x","BXD180":"x","BXD181":"x","BXD183":"x","BXD184":"x","BXD186":"x","BXD187":"x","BXD188":"x","BXD189":"x","BXD190":"x","BXD191":"x","BXD192":"x","BXD193":"x","BXD194":"x","BXD195":"x","BXD196":"x","BXD197":"x","BXD198":"x","BXD199":"x","BXD200":"x","BXD201":"x","BXD202":"x","BXD203":"x","BXD204":"x","BXD205":"x","BXD206":"x","BXD207":"x","BXD208":"x","BXD209":"x","BXD210":"x","BXD211":"x","BXD212":"x","BXD213":"x","BXD214":"x","BXD215":"x","BXD216":"x","BXD217":"x","BXD218":"x","BXD219":"x","BXD220":"x"}'

def simulated_form(corr_type: str = "sample"):
    assert corr_type in ("sample", "tissue", "lit")
    return {
            "dataset": "HC_M2_0606_P",
            "trait_id": "1435464_at",
            "corr_dataset": "HC_M2_0606_P",
            "corr_sample_method": "pearson",
            "corr_return_results": "100",
            "corr_samples_group": "samples_primary",
            "sample_vals": sample_vals(),
            "corr_type": corr_type,
            "corr_sample_method": "pearson",
            "location_type": "gene",
            "corr_return_results": "20000"
        }

def profile_corrs():
    "Profile tho correlations"
    profiler = cProfile.Profile()
    profiler.enable()
    correlation_results = compute_correlation(request.form, compute_all=True)
    profiler.disable()
    return profiler

def dump_stats(profiler):
    iostr = io.StringIO()
    sort_by = pstats.SortKey.CUMULATIVE
    ps = pstats.Stats(profiler, stream=iostr).sort_stats(sort_by)
    ps.print_stats()

    cli_args = sys.argv
    if len(cli_args) > 1:
        with open(cli_args[1], "w+", encoding="utf-8") as output_file:
            print(iostr.getvalue(), file=output_file)

        return 0

    print(iostr.getvalue())
    return 0


if __name__ == "__main__":
    def main():
        "Entry point for profiler script"
        return dump_stats(profile_corrs())

    with app.app_context():
        with app.test_request_context("/corr_compute", data=simulated_form()):
            g.user_session = UserSession()
            main()
