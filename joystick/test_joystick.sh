echo "Checking for existance of Joystick"

has_joystick_direct_mode=$(lsusb | grep "Logitech, Inc. Cordless RumblePad 2" | wc -l)
has_joystick_xinput_mode=$(lsusb | grep "F710 Wireless Gamepad \[XInput Mode\]" | wc -l)

if [ "$has_joystick_direct_mode" -gt 0 ]; then
    echo "... Found Joystick"
elif [ "$has_joystick_xinput_mode" -gt 0 ]; then
	echo "... Found Joystick, but it's in XInput mode, so toggle the switch on the back to the \"d\" position"
	exit 1
else
    echo "... JOYSTICK NOT FOUND. Make sure it's plugged in. Here's the lsusb output:"
    echo "$ lsusb"
    lsusb
    exit 1
fi

echo "Testing for Joystick functionality. Running jstest."

jstest_success=$(timeout 0.2 jstest --event /dev/input/joystick | head -n 5 | grep "has 6 axes" | wc -l)

if [ "$jstest_success" -gt 0 ]; then
    echo "... Received expected output from jstest, joystick working correctly!"
    exit 0
else
    echo "... Did not receive correct output from jstest. Use lsusb and jstest to investigate - the joystick should appear mounted at /dev/input/joystick"
    exit 1
fi