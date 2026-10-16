/* 로고 윗줄(한가람농업개발 / HANGARAM AGRI) 길이를 아래 Agrow 길이에 맞춤 */
(function(){
  var P=[['lg-k','lg-w'],['flg-k','flg-w']];
  function tw(el){var r=document.createRange();r.selectNodeContents(el);return r.getBoundingClientRect().width;}
  function fit(k,w){
    var n=Array.from(k.textContent.trim()).length;if(n<2)return;
    k.style.removeProperty('letter-spacing');k.style.removeProperty('font-size');
    k.style.setProperty('letter-spacing','0px','important');
    var lsW=parseFloat(getComputedStyle(w).letterSpacing)||0;
    var target=tw(w)-lsW, k0=tw(k);
    if(!target||!k0)return;
    var t=(target-k0)/(n-1);
    if(t>=0){k.style.setProperty('letter-spacing',t.toFixed(3)+'px','important');}
    else{var fs=parseFloat(getComputedStyle(k).fontSize);k.style.setProperty('font-size',(fs*target/k0).toFixed(3)+'px','important');}
  }
  function run(){P.forEach(function(p){document.querySelectorAll('.'+p[0]).forEach(function(k){var w=k.parentNode.querySelector('.'+p[1]);if(w)fit(k,w);});});}
  function init(){
    run();
    if(document.fonts&&document.fonts.ready)document.fonts.ready.then(run);
    var mo=new MutationObserver(run);
    P.forEach(function(p){document.querySelectorAll('.'+p[0]).forEach(function(k){mo.observe(k,{childList:true,characterData:true,subtree:true});});});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
