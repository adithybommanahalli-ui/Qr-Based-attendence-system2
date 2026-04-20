const FACE_API_MODELS_URL = 'https://cdn.jsdelivr.net/gh/justadudewhohacks/face-api.js@master/weights/';

async function loadFaceApiModels() {
  if (faceapi.nets.tinyFaceDetector.isLoaded &&
      faceapi.nets.faceLandmark68Net.isLoaded &&
      faceapi.nets.faceRecognitionNet.isLoaded) {
    return;
  }
  await Promise.all([
    faceapi.nets.tinyFaceDetector.loadFromUri(FACE_API_MODELS_URL),
    faceapi.nets.faceLandmark68Net.loadFromUri(FACE_API_MODELS_URL),
    faceapi.nets.faceRecognitionNet.loadFromUri(FACE_API_MODELS_URL)
  ]);
}

async function detectFaceDescriptor(videoElement) {
  const options = new faceapi.TinyFaceDetectorOptions({ inputSize: 320, scoreThreshold: 0.4 });
  const result = await faceapi
    .detectSingleFace(videoElement, options)
    .withFaceLandmarks()
    .withFaceDescriptor();
  if (!result) return null;
  return result.descriptor;
}
