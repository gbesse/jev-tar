"""Show why a zero-miss sample does not establish zero residual risk."""
import json

from jev_tar import elusion_estimate


def example():
    synthetic_human_sample = [{"human_responsive": "false"} for _ in range(100)]
    result = elusion_estimate(synthetic_human_sample, population_below=1000, reviewed_found=80)
    assert result["misses"] == 0
    assert result["missed_interval"][1] > 0
    return {
        "source": "synthetic human labels; no Jev calls or legal conclusion",
        "sample_size": result["sample"],
        "sampled_misses": result["misses"],
        "estimated_missed": result["estimated_missed"],
        "upper_interval_missed": result["missed_interval"][1],
    }


if __name__ == "__main__":
    print(json.dumps(example(), indent=2, sort_keys=True))
