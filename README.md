# Lab 3: Wall Following on the Racecar

It's time to use the actual racecar!
You will be taking the wall following code that you ran in simulation and running it on the car.
You will also be building a safety controller to prevent your racecar from crashing into obstacles.

## Disclaimer

The racecar platform is exciting and fast but it is not a toy.
The hardware we have on board is extremely expensive and it is your responsibility to keep it in good condition for future classes.
The racecar can survive a couple light bumps but if it goes flying into a wall it will not survive. The whole frame can split in half, the lidar can get scratched, the TX2 can get damaged, etc. Any one of these repairs can cost hudreds if not thousands of dollars.

If your car develops hardware issues for any reason, please tell the TAs and we will replace your car and then refurbish the damaged one. Most teams will probably have some hardware issue throughout the course and it is typically not a big deal.
But if you damage the car in an extreme way through obviously reckless behaviour you may find yourself working on the simulated car for the rest of the course.

## Electrical Safety

The racecar runs on relatively low voltage (< 24V) so we are not too concered about dangerous shocks.
But as with any electrical system it is always important to take proper safety precautions.
For example ground yourself before touching any of the exposed circuit boards like the TX2.

Please read and sign the electrical safety form here before starting work on the racecar:
https://eecs-ug.scripts.mit.edu:444/safety/index.py/6.141

## The Racecar

### Connections and Power

Plug your router into an outlet and use the ethernet cable to connect it to a working ethernet port (not all the ports in 32-080 work). 
Then connect to the Wi-Fi on your laptop.
The password is ```g0_fast!```.

Check the battery status on your racecar by pressing the power button on your black energizer battery. 
This power button is merely an indicator and does not actually power the battery on or off.
It is always on, so make sure you unplug the power cables when the car is not in use.
On the hokuyo cars the battery sits right on top of the car.
On the velodyne cars the battery is velcroed under the car (be careful when pulling it out).

If your energizer is low on battery, charge it with the adapter.
Note that the car will probably turn off when you disconnect the power adapter; during the switch back to battery power there is a moment where the TX2 does not have enough power to stay on.
You will need to disconnect the car from the power adapter when you want to drive it around.
The battery lasts a suprisingly long time, so as long as you keep the battery charged when you are not working it can last the entire lab.

Connect the two power cables to the energizer battery.
One powers the lidar and the TX2. 
The other powers the USB hub (which powers the ZED camera and IMU).
If everything is receiving power, you should see LEDs light up on the TX2 and IMU and you should hear the lidar spinning.
Power on the TX2 by pressing the rightmost button labeled "power".
The button should light up green.

### SSH

With everything powered on, you can connect directly to the car using:

    ssh racecar@[COREY_WHAT_IS_THE_IP]
    
The password is ```racecar@mit```. If you can't connect make sure you are still on the correct Wi-Fi network.

The car is running Ubuntu just like the virtual machine.
It should be familiar, but poke around to get comfortable with the structure.
Just like in the simulator, you will often need multiple terminal windows open in order to launch different ros nodes.
There are many ways to do this.

- Open multiple windows on your local machine and ```ssh racecar@[COREY_WHAT_IS_THE_IP]``` in each one of them. You can even ssh from multiple computers at the same time but make sure you are communicating with your team members.
- Use [screen](https://kb.iu.edu/d/acuy) to open layered windows in terminal and navigate through them with key commands.
- Use ```ssh``` with the ```-X``` flag to enable X11 forwarding. With this flag you can launch graphical programs in the ssh client and have them displayed on your local machine. For example you could run ```xterm &``` to get a new terminal window. Or you could run ```i3 &``` to get a tiling window manager. X11 Forwarding can take up more bandwidth so avoid it if your connection is poor.

### Manual Navigation

When you are ready, disconnect the power adapters to the energizer and motors and plug the motors in.
Turn on and recconect to the racecar if necessary.
Get the car to a safe place (_not on a table!_) and launch teleop just like in the simulator:

    roslaunch racecar teleop

Now you should be able to move the car around with the joystick!
Your computer will disconnect from the racecar if it gets too far away from the router, but the code running on it will not be affected.

## Wall Following

Use ```scp``` or ```git clone``` to get one of your team members' wall following code from lab 2 onto the car. 
Get the car into a safe location and make sure ```teleop``` is running. In another terminal launch

    roslaunch wall_follower wall_follower.launch
    
Hopefully this will work without any changes!
If nessesary tune the parameters in the wall follower so that it works well in real life.
Try combining ideas from multiple team members' implimentations of the wall follower to make a more robust controller.

## Safety Controller

Now that you’ve got your wall follower working we want you to build a safety controller.
In future labs the racecar will be moving at high speeds so we need you to build a system that protects it from crashes. 

The racecar has a command mux with different levels of priority.
The navigation mux you have been publishing to has the lowest priority:

    /vesc/ackermann_cmd_mux/input/navigation
    
The joystick has higher priority and commands published to this topic will override commands sent to navigation:

    /vesc/ackermann_cmd_mux/input/teleop
    
The highest priority mux that we have set up is the safety mux. Commands sent here will override all other steering commands.

    /vesc/ackermann_cmd_mux/input/safety
    
Write a node that publishes to the safety mux in order to prevent the racecar from running into obstacles.

We want you to be able to demonstrate that your safety controller is robust. You should be able to use the joystick to attempt to crash the racecar in a variety of senarioes and have the safety controller prevent the crashes. You should also be able to walk in front of the racecar without it running into you. _Please be careful as you are testing; start slow._

At the same time your racecar should not be "scared". You should still be able to drive close to walls, turn around corners, go fast etc. without the racecar freezing in it's tracks. You will be required to run your safety controller in all future labs so don't cripple yourself with something overprotective.

## Deliverables

From now on your lab deliverables will consist of two parts; a presentation and a lab report.
Make sure that in each you demonstrate your ability to 

- Log into the physical car and manually drive.
- Autonomously drive the racecar with your wall following code.
- Prevent crashes using your safety controller while maintaining flexibility.

Use of video, screen shots, etc. is highly recommended.
