<div align="center" margin-bottom="20px">
  <strong><h1>Satellite Image Analysis</h1></strong>
</div>
<div>
  This repository contains three type of works
  <ol type='1'>
    <li><a href="https://github.com/AgileCrafts/Satellite-Image-Analysis/tree/main/Manual%20Detection">Manual Detection</a></li>
    <li><a href="https://github.com/AgileCrafts/Satellite-Image-Analysis/tree/main/Vessel%20Detection%20with%20YOLOv11%20(tiling%2C%20super%20resolution)">Boat Detection Algorithms</a></li>
    <li><a href="https://github.com/AgileCrafts/Satellite-Image-Analysis/tree/main/app">Application</a></li>
  </ol>
  <div>
    <h2>Manual Detection</h2>
    <p>This work contains detection of water in certain areas to mark water encroachment. Here, MNDWI is used with other libraries to perfectly detect water surface. In here, requirements are given in config file and sentinel-2 images are downloaded using sentinel hub when run.py file is execcuted. Another seperate file called "pre-post rgb image downloader" downloads RGB images for pre and post dates. The water analysis file then completes the analysis and a collage image is also generated for better visualization. Downloaded images are stored into downloads folder according to their dates and the results are saved in the folder 'wadownloads'.</p>
  </div>


  <div>
    <h2>Boat Detection Algorithms</h2>
    <p>This work contains same methods as water detection with some super resolution and vessel detection techniques.There is also tiling technique which didn't work well in this case. These techniques are stored in seperate files of water analysis.</p>
  </div>
  
</div>
