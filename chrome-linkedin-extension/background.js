// Copyright 2018 The Chromium Authors. All rights reserved.
// Use of this source code is governed by a BSD-style license that can be
// found in the LICENSE file.

'use strict';

function downloadObjectAsJson(exportObj, exportName) {
  var dataStr =
    'data:text/json;charset=utf-8,' +
    encodeURIComponent(JSON.stringify(exportObj));
  var downloadAnchorNode = document.createElement('a');
  downloadAnchorNode.setAttribute('href', dataStr);
  downloadAnchorNode.setAttribute('download', exportName + '.json');
  document.body.appendChild(downloadAnchorNode);
  downloadAnchorNode.click();
  downloadAnchorNode.remove();
}

function doStuffWithResponse(response) {
    console.log("I got the following response:");
    console.log(response);
    downloadObjectAsJson(response, response.name + "-linkedin.json");
    const test_url = "http://127.0.0.1:5000/api/linkedin";
    const url = "https://friendforce-server.herokuapp.com/api/linkedin"
    fetch(url, {
      method : "POST",
      body : JSON.stringify({
         data : response,
      })
    }).then(
      serverResponse => {
        return serverResponse.json();} // .json(), etc.
    ).then(
      json => {console.log(JSON.stringify(json));}
    );
  }



chrome.browserAction.onClicked.addListener(function(tab) {
  chrome.tabs.sendMessage(tab.id, {text: 'report_back'}, doStuffWithResponse);

});
