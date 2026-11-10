(function () {
  var cfg = window.SITE_CONFIG || {};

  // Sticky nav: darken and blur once the page scrolls.
  var head = document.querySelector('.site-head');
  if (head) {
    var onScroll = function () { head.classList.toggle('is-stuck', window.scrollY > 8); };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  // Amazon tag: build.py bakes it in; this keeps links right if config.js changes before a rebuild.
  if (cfg.AMAZON_TAG) {
    document.querySelectorAll('a[data-amazon]').forEach(function (a) {
      try {
        var u = new URL(a.href);
        u.searchParams.set('tag', cfg.AMAZON_TAG);
        a.href = u.toString();
      } catch (e) {}
    });
  }

  // AdSense: slots stay hidden and empty unless a client id is configured.
  if (cfg.ADSENSE_CLIENT) {
    var slots = document.querySelectorAll('.ad-slot');
    if (slots.length) {
      var s = document.createElement('script');
      s.async = true;
      s.crossOrigin = 'anonymous';
      s.src = 'https://pagead2.googlesyndication.com/pagead/js/adsbygoogle.js?client=' + encodeURIComponent(cfg.ADSENSE_CLIENT);
      document.head.appendChild(s);
      slots.forEach(function (slot) {
        var ins = document.createElement('ins');
        ins.className = 'adsbygoogle';
        ins.style.display = 'block';
        ins.setAttribute('data-ad-client', cfg.ADSENSE_CLIENT);
        ins.setAttribute('data-ad-format', 'auto');
        ins.setAttribute('data-full-width-responsive', 'true');
        slot.appendChild(ins);
        slot.classList.add('filled');
        (window.adsbygoogle = window.adsbygoogle || []).push({});
      });
    }
  }

  // Contact page: HubSpot form when a form id is set, else email fallback.
  var contact = document.getElementById('contact-target');
  if (contact) {
    if (cfg.HUBSPOT_PORTAL && cfg.HUBSPOT_FORM_ID) {
      var hs = document.createElement('script');
      hs.src = 'https://js.hsforms.net/forms/embed/v2.js';
      hs.onload = function () {
        if (window.hbspt) window.hbspt.forms.create({ portalId: cfg.HUBSPOT_PORTAL, formId: cfg.HUBSPOT_FORM_ID, target: '#contact-target' });
      };
      document.body.appendChild(hs);
    } else if (cfg.CONTACT_EMAIL) {
      var a = document.createElement('a');
      a.href = 'mailto:' + cfg.CONTACT_EMAIL;
      a.textContent = cfg.CONTACT_EMAIL;
      contact.textContent = 'Email: ';
      contact.appendChild(a);
    }
  }
})();
