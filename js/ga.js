/* Google Analytics 4 — 측정 ID는 여기 한 곳에서만 관리 */
(function(){
  var ID='G-8B8FRZMWZF';
  window.dataLayer=window.dataLayer||[];
  function gtag(){dataLayer.push(arguments);}
  window.gtag=gtag;
  gtag('js',new Date());
  gtag('config',ID,{anonymize_ip:true});
  var s=document.createElement('script');s.async=true;s.src='https://www.googletagmanager.com/gtag/js?id='+ID;
  (document.head||document.documentElement).appendChild(s);
  function lang(){return document.documentElement.lang||'';}
  window.agTrack=function(name,params){try{params=params||{};params.page_lang=lang();gtag('event',name,params);}catch(e){}};
  /* 문의 버튼 / 언어 변경 / 카탈로그 클릭 자동 집계 */
  document.addEventListener('click',function(e){
    var a=e.target.closest&&e.target.closest('a,button');if(!a)return;
    var h=a.getAttribute('href')||'';
    if(h.indexOf('tel:')===0)agTrack('contact_click',{method:'phone'});
    else if(h.indexOf('mailto:')===0)agTrack('contact_click',{method:'email'});
    else if(h.indexOf('t.me/')>-1)agTrack('contact_click',{method:'telegram'});
    else if(/catalog\.html/.test(h))agTrack('catalog_open',{link_url:h});
    if(a.classList&&a.classList.contains('lang-opt')&&a.dataset.lang)agTrack('language_change',{language:a.dataset.lang});
    if(a.hasAttribute&&a.hasAttribute('hreflang')&&a.closest('.lsel'))agTrack('language_change',{language:a.getAttribute('lang')});
  },true);
})();
