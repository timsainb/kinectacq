Usage
=======================

Acquisition is run through the ``start_recording`` function, which can
be found in the ``run_azures`` Jupyter notebook.

Briefly, for each camera, a k4a object is created, and a seperate
acquisition process running the function ``capture_from_azure`` is
opened. The function loops continuously over a set duration, sampling
depth, ir, and camera data. Synchronization over cameras is handled by a
master-subordinate system, offsetting sampling between each camera.

.. figure:: ../files/Azure-acquisition.png
   :alt: Acqusition pipeline

   Acqusition pipeline