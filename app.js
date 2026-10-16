const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];
const query = new URLSearchParams(location.search);

const trackMeta = (event, params={}, options={}) => {
  if (typeof window.fbq !== 'function') return;
  window.fbq('track', event, params, options);
};

const trackMetaCustom = (event, params={}) => {
  if (typeof window.fbq !== 'function') return;
  window.fbq('trackCustom', event, params);
};

trackMeta('ViewContent', {
  content_name: '鄉民首贏建案頁',
  content_category: '新竹東區學區宅'
});

const header = $('.site-header');
window.addEventListener('scroll', () => header.classList.toggle('scrolled', scrollY > 30), {passive:true});

$$('.plan-tab').forEach(btn => btn.addEventListener('click', () => {
  $$('.plan-tab').forEach(x => { x.classList.remove('active'); x.setAttribute('aria-selected','false'); });
  $$('.plan-panel').forEach(x => x.classList.remove('active'));
  btn.classList.add('active'); btn.setAttribute('aria-selected','true');
  $('#plan-' + btn.dataset.plan).classList.add('active');
}));

$$('.choose-plan').forEach(btn => btn.addEventListener('click', () => {
  $('#unitSelect').value = btn.dataset.choice;
  $('#reserve').scrollIntoView({behavior:'smooth'});
  setTimeout(() => $('[name="name"]').focus(), 500);
}));

$$('a[href="#reserve"]').forEach(link => link.addEventListener('click', () => {
  trackMetaCustom('ReserveIntent', {button_text: link.textContent.trim()});
}));

$$('a[href^="tel:"]').forEach(link => link.addEventListener('click', () => {
  trackMeta('Contact', {contact_method: 'phone'});
}));

const imageDialog = $('#imageDialog');
$('.image-zoom')?.addEventListener('click', e => {
  $('img', imageDialog).src = e.currentTarget.dataset.src;
  imageDialog.showModal();
});
$$('.dialog-close').forEach(btn => btn.addEventListener('click', () => btn.closest('dialog').close()));
$$('dialog').forEach(d => d.addEventListener('click', e => { if (e.target === d) d.close(); }));

const form = $('#reservationForm');
const statusEl = $('#formStatus');
const successDialog = $('#successDialog');
let formStarted = false;
form.addEventListener('focusin', () => {
  if (formStarted) return;
  formStarted = true;
  trackMetaCustom('FormStart', {form_name: '索取建案資料'});
});
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = '';
  if (!form.reportValidity()) return;
  const fd = new FormData(form);
  const payload = Object.fromEntries(fd.entries());
  payload.consent = fd.get('consent') === 'on';
  payload.source = [
    query.get('utm_source') || 'website',
    query.get('utm_campaign') ? `cmp:${query.get('utm_campaign')}` : '',
    query.get('utm_content') ? `ad:${query.get('utm_content')}` : ''
  ].filter(Boolean).join('|').slice(0, 100);
  payload.page = location.href;
  const btn = $('.submit-btn', form), text = $('.submit-text', btn), spinner = $('.spinner', btn);
  btn.disabled = true; text.hidden = true; spinner.hidden = false;
  try {
    const res = await fetch('/api/reservations', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || '送出失敗，請稍後再試');
    $('#reservationId').textContent = data.reservation_id || '已建立';
    trackMeta('Lead', {
      content_name: '索取格局與價目',
      content_category: '鄉民首贏'
    }, {eventID: data.reservation_id || undefined});
    form.reset();
    successDialog.showModal();
  } catch (err) {
    statusEl.textContent = err.message + '；也可直接撥打 0916882564 王小姐。';
  } finally {
    btn.disabled = false; text.hidden = false; spinner.hidden = true;
  }
});
