 function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function addSideBarImage() {
  var stream = document.getElementById("remoteVideosContainer").children[0];
  stream.style.position = 'relative';
  var img = document.createElement('img');
  img.src = 'https://www.carebyfern.com/static/giver/img/new_sidebar_mock.png';
  img.style.maxWidth = '100%';
  img.style.height = '100%';
  img.style.marginLeft = '-10%';
  img.style.zIndex = 98;
  var remoteVideosContainer = document.getElementById("remoteVideosContainer");
  remoteVideosContainer.style.display = 'flex';
  remoteVideosContainer.style.alignItems = 'center';
  remoteVideosContainer.style.justifyContent = 'center';
  remoteVideosContainer.appendChild(img);

  var localVideo = document.getElementById("localVideo"); 
  localVideo.style.opacity = 0;
}

function addLocalMap() {
  var img2 = document.createElement('img');
  img2.src = 'https://www.carebyfern.com/static/giver/img/static_map.png';
  var remoteVideosContainer = document.getElementById("remoteVideosContainer");
  remoteVideosContainer.prepend(img2);
  img2.style.height = '30%';
  img2.style.marginRight = '-37.5%';
  img2.style.zIndex = 99;
}

function addLogos(){
  var img3 = document.createElement('img');
  img3.src = 'https://www.carebyfern.com/static/giver/img/logos.png';
  img3.style.position = 'absolute';
  img3.style.zIndex = 97;
  img3.style.top = '60px';
  img3.style.marginRight = '-20px';
  var remoteVideosContainer = document.getElementById("remoteVideosContainer");
  remoteVideosContainer.prepend(img3);
}

function addImageToTopBar(url) {
  var image = document.createElement('img');
  image.src = url;
  image.style.width = '20px';
  document.getElementById("overlay-top").appendChild(image);
};

function addElementToOverlay() {
  newDiv = document.createElement('div');
  newDiv.classList.add("ovl-horiz");
}

var recording = false;
async function demo() {
   console.log("test");
     // Get a MediaStream object to record
    // and pass it to MediaRecorder constructor
    // to create a MediaRecorder instance `recorder`
    const stream = document.getElementById("remoteVideosContainer").children[0].captureStream();
    var options = {mimeType:'video/mp4'};
    const recorder = new MediaRecorder(stream, options);

    // When recording starts, the captured frames are emitted
    // as `dataavailable` events on the `recorder`.
    // These captured "chunks" can be collected in an array.
    const allChunks = [];
    recorder.ondataavailable = function(e) {
      allChunks.push(e.data);
    }

    // Start recording
    recorder.start();
    console.log('Taking a break...');
    // We can pause capturing media and resume again later
    // to deal with irregular media playback
    // (likely due to user interactions or buffering)
    //recorder.pause();
    //recorder.resume();

    // When we're done, we can stop recording.
    // This ensures that no more media chunks are captured,
    // even if media playback continues.
    await sleep(2000);
    console.log('Two second later');
    recorder.stop();
    // TODO need to record chunks
    // We can now join all the chunks
    // into a single "blob" ...
    const fullBlob = new Blob(allChunks);

    // ... which we can download using HTML5 `download` attribute on <a />
    const link = document.createElement('a');
    link.style.display = 'none';

    const downloadUrl = window.URL.createObjectURL(fullBlob);
    link.href = downloadUrl;
    link.download = 'media.webm';

    document.body.appendChild(link);
    link.click();
    link.remove();  
}

addButton = (recorder) => {
  let button = document.createElement('button');
  button.style.backgroundColor = 'red';
  button.addEventListener('click', function() {
    console.log("BUTTON CLICKED");
    if (!recording) {
      recording = true;
      recorder.start();
      console.log('recording');
    } else  if (recording) {
      recording = false;
      recorder.stop();

      // We can now join all the chunks
      // into a single "blob" ...
      const fullBlob = new Blob(allChunks);

      // ... which we can download using HTML5 `download` attribute on <a />
      const link = document.createElement('a');
      link.style.display = 'none';

      const downloadUrl = window.URL.createObjectURL(fullBlob);
      link.href = downloadUrl;
      link.download = 'media.webm';

      document.body.appendChild(link);
      link.click();
      link.remove(); 
    }
  });
  document.getElementById("overlay-top").appendChild(button);
}


const stream = document.getElementById("remoteVideosContainer").children[0].captureStream();
//var options = {mimeType:'video/mp4'};
const recorder = new MediaRecorder(stream);

// When recording starts, the captured frames are emitted
// as `dataavailable` events on the `recorder`.
// These captured "chunks" can be collected in an array.
const allChunks = [];
recorder.ondataavailable = function(e) {
  allChunks.push(e.data);
}
addButton(recorder);
addSideBarImage();
addLocalMap();
//addLogos();





