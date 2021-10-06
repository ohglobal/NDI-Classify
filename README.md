# NDI-Classify
A program for recognizing objects in NDI sources with Tensorflow

Basically, you download your tensorflow model from somewhere like teachable machine, toss it next to my program here, and then follow the prompts to identify which NDI sources you want to look at and where to send the OSC predictions to. Teachable Machine is by far the easiest system ive encountered for training recognition models. it's super user friendly and within moments you can have a robust, multi class tensorflow model ready to rock with zero code.

I built this app for a friend who is doing a piece of theater that involves people walking around pointing their phones at various objects in their surroundings. They do this on Zoom, then ZoomISO pulls the NDI stems into this app, which spits OSC back to Isadora to trigger events, visuals, and sounds in the meeting
