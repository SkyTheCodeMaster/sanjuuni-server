# sanjuuni-server
## A free, opensource sanjuuni server.

How to use:
POST to `/convert` with the following JSON: 
```json
{
  "url":"url of image to convert", // OR
  "data": "base64 bytes of image to convert", // One or the other, not both.

  // Sanjuuni options (ALL OPTIONAL)
  "dithering": "none", // None default, options: "threshold","ordered","lab-color","octree","kmeans","none"
  "binary": false, // Boolean, whether or not returned file is binary.
  "width": 51, // Resize image to this width/height
  "height": 19,
  "cc-palette": false, // Boolean, whether or not to generate custom palette, or use CC colours.
  "format": "bimg" // String, blit default, options: "bimg","nfp"
}
```
The server will process and then return a **blit image (bimg)** of the input image.