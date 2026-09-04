const $ = (s, root=document) => root.querySelector(s);
const $$ = (s, root=document) => [...root.querySelectorAll(s)];

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
form.addEventListener('submit', async (e) => {
  e.preventDefault();
  statusEl.textContent = '';
  if (!form.reportValidity()) return;
  const fd = new FormData(form);
  const payload = Object.fromEntries(fd.entries());
  payload.consent = fd.get('consent') === 'on';
  payload.source = new URLSearchParams(location.search).get('utm_source') || 'website';
  payload.page = location.href;
  const btn = $('.submit-btn', form), text = $('.submit-text', btn), spinner = $('.spinner', btn);
  btn.disabled = true; text.hidden = true; spinner.hidden = false;
  try {
    const res = await fetch('/api/reservations', {method:'POST', headers:{'Content-Type':'application/json'}, body:JSON.stringify(payload)});
    const data = await res.json().catch(() => ({}));
    if (!res.ok) throw new Error(data.error || '送出失敗，請稍後再試');
    $('#reservationId').textContent = data.reservation_id || '已建立';
    form.reset();
    successDialog.showModal();
  } catch (err) {
    statusEl.textContent = err.message + '；也可直接撥打 0916882564 王小姐。';
  } finally {
    btn.disabled = false; text.hidden = false; spinner.hidden = true;
  }
});
