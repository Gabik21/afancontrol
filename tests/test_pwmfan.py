from contextlib import ExitStack

import pytest

from afancontrol.pwmfan import PWMFanNorm


@pytest.fixture
def pwm_path(temp_path):
    # pwm = /sys/class/hwmon/hwmon0/pwm2
    pwm_path = temp_path / "pwm2"
    pwm_path.write_text("0\n")
    return pwm_path


@pytest.fixture
def pwm_enable_path(temp_path):
    pwm_enable_path = temp_path / "pwm2_enable"
    pwm_enable_path.write_text("0\n")
    return pwm_enable_path


@pytest.fixture
def fan_input_path(temp_path):
    # fan_input = /sys/class/hwmon/hwmon0/fan2_input
    fan_input_path = temp_path / "fan2_input"
    fan_input_path.write_text("1300\n")
    return fan_input_path


@pytest.fixture
def pwmfan_norm(pwm_path, fan_input_path):
    return PWMFanNorm(
        pwm=str(pwm_path),
        fan_input=str(fan_input_path),
        pwm_line_start=100,
        pwm_line_end=240,
        never_stop=False,
    )


def test_get_speed(pwmfan_norm, fan_input_path):
    fan_input_path.write_text("721\n")
    assert 721 == pwmfan_norm.get_speed()


@pytest.mark.parametrize("raises", [True, False])
def test_enter_exit(raises, pwmfan_norm, pwm_enable_path, pwm_path):
    class Exc(Exception):
        pass

    with ExitStack() as stack:
        if raises:
            stack.enter_context(pytest.raises(Exc))
        stack.enter_context(pwmfan_norm)

        assert "1" == pwm_enable_path.read_text()
        assert "255" == pwm_path.read_text()
        value = 0.39  # 100/255 ~= 0.39
        pwmfan_norm.set(value)
        if raises:
            raise Exc()

    assert "0" == pwm_enable_path.read_text()
    assert "100" == pwm_path.read_text()


def test_get_set_pwmfan(pwmfan_norm, pwm_path):
    pwmfan_norm._set_raw(142)
    assert "142" == pwm_path.read_text()

    pwm_path.write_text("132\n")
    assert 132 == pwmfan_norm._get_raw()

    pwmfan_norm.set_full_speed()
    assert "255" == pwm_path.read_text()

    with pytest.raises(ValueError):
        pwmfan_norm._set_raw(256)

    with pytest.raises(ValueError):
        pwmfan_norm._set_raw(-1)


def test_get_set_pwmfan_norm(pwmfan_norm, pwm_path):
    pwmfan_norm.set(0.42)
    assert "101" == pwm_path.read_text()

    pwm_path.write_text("132\n")
    assert pytest.approx(0.517, 0.01) == pwmfan_norm.get()

    pwmfan_norm.set_full_speed()
    assert "255" == pwm_path.read_text()

    assert 240 == pwmfan_norm.set(1.1)
    assert "240" == pwm_path.read_text()

    assert 0 == pwmfan_norm.set(-0.1)
    assert "0" == pwm_path.read_text()
