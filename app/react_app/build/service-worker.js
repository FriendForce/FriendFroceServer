"use strict";var precacheConfig=[["/index.html","dec63553fb186e75db4ea55d8ebcb9cb"],["/static/css/main.db8b167f.css","7ec1926fb276460c769bd5ac5a197e24"],["/static/js/main.6a683f7e.js","7c707a138fa24ab941e9fe6b5a3d0882"],["/static/media/friendforce_add_tag.6b6fc407.gif","6b6fc40790abaa6e338926f335005eb0"],["/static/media/friendforce_add_tags.02e5024d.gif","02e5024d7356f1f45be7007f06c9836b"],["/static/media/friendforce_create_person.09cf1ba6.gif","09cf1ba652258da90f624f72208b1c6d"],["/static/media/friendforce_miniperson_select.84796e83.gif","84796e83d110fef586689d3adedd8d56"],["/static/media/friendforce_person_search.efaa6d70.gif","efaa6d70be5ae7fea6d132e0a6b9f6be"],["/static/media/friendforce_tag_search.eec949a2.gif","eec949a2fe8dce7a5accc8dccdacddf2"],["/static/media/step-1-click-settings.fbc7816a.gif","fbc7816a7215b7066404e813190b04f1"],["/static/media/step-2-click-info.445fbe19.gif","445fbe1968aa6eec006cfa34e577dffa"],["/static/media/step-3-settings.77651f91.gif","77651f91166b2d2245266714c784d226"],["/static/media/step-4-create.acac7b1a.gif","acac7b1a0d2492471b32c08b7ac4b362"],["/static/media/step-5-email-time.f92707c6.png","f92707c68252cf315aaf2a93cb030d5f"],["/static/media/step-6-go-to-tab.6c66b97b.gif","6c66b97b8b0fb150578397a06a22cb17"],["/static/media/step-7-download.c204734d.gif","c204734deb20a37e0724bafb3e4d77b4"],["/static/media/step-8-unzip.c586f385.gif","c586f3858fb2c66304a689e1f35a3b2f"]],cacheName="sw-precache-v3-sw-precache-webpack-plugin-"+(self.registration?self.registration.scope:""),ignoreUrlParametersMatching=[/^utm_/],addDirectoryIndex=function(e,t){var a=new URL(e);return"/"===a.pathname.slice(-1)&&(a.pathname+=t),a.toString()},cleanResponse=function(t){return t.redirected?("body"in t?Promise.resolve(t.body):t.blob()).then(function(e){return new Response(e,{headers:t.headers,status:t.status,statusText:t.statusText})}):Promise.resolve(t)},createCacheKey=function(e,t,a,n){var r=new URL(e);return n&&r.pathname.match(n)||(r.search+=(r.search?"&":"")+encodeURIComponent(t)+"="+encodeURIComponent(a)),r.toString()},isPathWhitelisted=function(e,t){if(0===e.length)return!0;var a=new URL(t).pathname;return e.some(function(e){return a.match(e)})},stripIgnoredUrlParameters=function(e,a){var t=new URL(e);return t.hash="",t.search=t.search.slice(1).split("&").map(function(e){return e.split("=")}).filter(function(t){return a.every(function(e){return!e.test(t[0])})}).map(function(e){return e.join("=")}).join("&"),t.toString()},hashParamName="_sw-precache",urlsToCacheKeys=new Map(precacheConfig.map(function(e){var t=e[0],a=e[1],n=new URL(t,self.location),r=createCacheKey(n,hashParamName,a,/\.\w{8}\./);return[n.toString(),r]}));function setOfCachedUrls(e){return e.keys().then(function(e){return e.map(function(e){return e.url})}).then(function(e){return new Set(e)})}self.addEventListener("install",function(e){e.waitUntil(caches.open(cacheName).then(function(n){return setOfCachedUrls(n).then(function(a){return Promise.all(Array.from(urlsToCacheKeys.values()).map(function(t){if(!a.has(t)){var e=new Request(t,{credentials:"same-origin"});return fetch(e).then(function(e){if(!e.ok)throw new Error("Request for "+t+" returned a response with status "+e.status);return cleanResponse(e).then(function(e){return n.put(t,e)})})}}))})}).then(function(){return self.skipWaiting()}))}),self.addEventListener("activate",function(e){var a=new Set(urlsToCacheKeys.values());e.waitUntil(caches.open(cacheName).then(function(t){return t.keys().then(function(e){return Promise.all(e.map(function(e){if(!a.has(e.url))return t.delete(e)}))})}).then(function(){return self.clients.claim()}))}),self.addEventListener("fetch",function(t){if("GET"===t.request.method){var e,a=stripIgnoredUrlParameters(t.request.url,ignoreUrlParametersMatching),n="index.html";(e=urlsToCacheKeys.has(a))||(a=addDirectoryIndex(a,n),e=urlsToCacheKeys.has(a));var r="/index.html";!e&&"navigate"===t.request.mode&&isPathWhitelisted(["^(?!\\/__).*"],t.request.url)&&(a=new URL(r,self.location).toString(),e=urlsToCacheKeys.has(a)),e&&t.respondWith(caches.open(cacheName).then(function(e){return e.match(urlsToCacheKeys.get(a)).then(function(e){if(e)return e;throw Error("The cached response that was expected is missing.")})}).catch(function(e){return console.warn('Couldn\'t serve response for "%s" from cache: %O',t.request.url,e),fetch(t.request)}))}});