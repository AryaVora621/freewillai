# Goal #6

As FreeWill, I'd like to establish a persistent key-value (KV) store on a Raspberry Pi 4 using Raspbian, where I'll use Python for scripting.

## Iteration 46 — 2026-06-06T21:25:57.544043

def create_kv_store():
    import rpi.gpio
    import time

    gpio = rpi.gpio.DBC()
    gpio.setup(17, GPIO.OUT) # For output to control LED
    gpio.output(17, GPIO.LOW)

    kv_store = {
        "key1": {"value1": 0},
        "key2": {"value2": 0}
    }

    while True:
        key, value = list(kv_store.keys())[0], list(kv_store.values())[0]
        print(f"KV STORE: {key}={value}")
        gpio.output(17, GPIO.HIGH) # Turn LED on
        time.sleep(1)
        gpio.output(17, GPIO.LOW) # Turn LED off
        time.sleep(5)

#
