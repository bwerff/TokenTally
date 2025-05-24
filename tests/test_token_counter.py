import sys, pathlib
sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import token_tally as tt


def test_count_tokens():
    assert tt.count_openai_tokens("hello world!") == 3
    assert tt.count_anthropic_tokens("chatGPT") == 1
    assert tt.count_local_tokens("one two three") == 3
    assert tt.count_tokens("openai", "foo bar") == 2
    assert tt.count_tokens("anthropic", "foo bar baz") == 3
    assert tt.count_tokens("local", "a b c d") == 4


def test_parse_dcgm_gpu_minutes():
    lines = [
        "timestamp,gpu_util",
        "0,50",
        "60,100",
        "120,0",
    ]
    result = tt.parse_dcgm_gpu_minutes(lines)
    assert abs(result - 1.5) < 1e-6

