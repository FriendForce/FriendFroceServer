// Listen for messages
console.log("listening for messages");
chrome.runtime.onMessage.addListener(function (msg, sender, sendResponse) {

  console.log("got message ");
  console.log(msg);
  var expand_buttons = Array.from(document.getElementsByClassName("pv-profile-section__see-more-inline pv-profile-section__text-truncate-toggle link"));
  expand_buttons.forEach(button=>{
    console.log(button);
    if (button.innterText) {
      if( button.innerText.includes("experience")) {
        console.log("more experience");
        button.click();
      }
    }
  });
  //Main Stuff
  var location = '';
  if (document.getElementsByClassName("pv-top-card-section__location")[0]) {
    location = document.getElementsByClassName("pv-top-card-section__location")[0].innerText;
  }
  var name = '';
  if (document.getElementsByClassName("pv-top-card-section__name")[0]) {
    name = document.getElementsByClassName("pv-top-card-section__name")[0].innerText;
  }
  var separation='';
  if (document.getElementsByClassName("pv-top-card-section__distance-badge")[0]) {
    separation = document.getElementsByClassName("pv-top-card-section__distance-badge")[0].getElementsByClassName("dist-value")[0].innerText;
  }
  var image = '';
  if (document.getElementsByClassName("pv-top-card-section__photo")[0]) {
    image = document.getElementsByClassName("pv-top-card-section__photo")[0].style.backgroundImage;
  }
  var contactInfo = '';
  if (document.getElementsByClassName("pv-top-card-v2-section__link--contact-info")[0]) {
    var contactInfo =  document.getElementsByClassName("pv-top-card-v2-section__link--contact-info")[0].href;
  }
  // Work Section
  var experiences = [];
  var experience = document.getElementById("experience-section");
  var experienceSections = Array.from(experience.getElementsByClassName("pv-profile-section__list-item"));
  experienceSections.forEach((section)=>{
    var experienceObject = {};
    if (section.getElementsByClassName("t-bold")[0]){
      experienceObject.title = section.getElementsByClassName("t-bold")[0].innerText;
    }
    if (section.getElementsByClassName("pv-entity__secondary-title")[0]) {
      experienceObject.company = section.getElementsByClassName("pv-entity__secondary-title")[0].innerText;
    }
    if (section.getElementsByClassName("pv-entity__location")[0]) {
      experienceObject.location = section.getElementsByClassName("pv-entity__location")[0].children[1].innerText;
    }
    if(section.getElementsByClassName("pv-entity__date-range")[0]) {
      experienceObject.dateRange = section.getElementsByClassName("pv-entity__date-range")[0].children[1].innerText;
    }
    experienceObject.locationCurrent = false;
    if (experienceObject.dateRange.includes("resent")) {
      experienceObject.locationCurrent = true;
    }
    experiences.push(experienceObject);
  });

  // Education Section
  var educations = []
  var education = document.getElementById("education-section");

  var educationSections = [];
  if (education) {
    educationSections = Array.from(education.getElementsByClassName("pv-profile-section__list-item"));
  }

  educationSections.forEach((section)=> {
    var educationObject = {};
    if (section.getElementsByClassName("pv-entity__school-name")[0]){
      educationObject.schoolName = section.getElementsByClassName("pv-entity__school-name")[0].innerText;
    }

    if ( section.getElementsByClassName("pv-entity__degree-name")[0]) {
      educationObject.degree = section.getElementsByClassName("pv-entity__degree-name")[0].innerText;
    }

    if(section.getElementsByClassName("pv-entity__extra-details")[0]) {
      educationObject.extraDetails = section.getElementsByClassName("pv-entity__extra-details")[0].innerText
    }
    if (section.getElementsByClassName("pv-entity__fos")[0]){
      educationObject.fieldOfStudy = section.getElementsByClassName("pv-entity__fos")[0].innerText;
    }
    if (section.getElementsByClassName("pv-entity__dates")[0]) {
      var start = section.getElementsByClassName("pv-entity__dates")[0].getElementsByTagName("time")[0].innerText;
      var stop = section.getElementsByClassName("pv-entity__dates")[0].getElementsByTagName("time")[1].innerText;
      educationObject.dateRange = start + "-" + stop;
    }

    educations.push(educationObject);
  });

  sendResponse({contactInfo:contactInfo, location:location, name:name, separation:separation, image:image, education:educations, experience:experiences});


});
