const sourceForm = document.querySelector('#source-form');
const urlInput = document.querySelector('#play-url');
const sourceFeedback = document.querySelector('#source-feedback');
const uploadInput = document.querySelector('#pdf-upload');
const plotView = document.querySelector('#plot-view');
const tableView = document.querySelector('#table-view');

sourceForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const hasSource = urlInput.value.trim().length > 0;
  sourceFeedback.textContent = hasSource ? 'ANALYSIS QUEUED / SAMPLE OUTPUT RETAINED' : 'ERROR / SOURCE REQUIRED';
  sourceFeedback.style.color = hasSource ? 'var(--green)' : 'var(--red)';
  if (hasSource) document.querySelector('#analysis-heading').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

document.querySelector('.clear-button').addEventListener('click', () => {
  urlInput.value = '';
  sourceFeedback.textContent = '';
  urlInput.focus();
});

uploadInput.addEventListener('change', () => {
  const file = uploadInput.files[0];
  if (!file) return;
  sourceFeedback.textContent = `ATTACHED / ${file.name.toUpperCase()}`;
  sourceFeedback.style.color = 'var(--green)';
});

document.querySelectorAll('.view-tab').forEach((tab) => {
  tab.addEventListener('click', () => {
    document.querySelectorAll('.view-tab').forEach((item) => item.classList.remove('active'));
    tab.classList.add('active');
    const tableSelected = tab.dataset.view === 'table';
    plotView.classList.toggle('hidden', tableSelected);
    tableView.classList.toggle('hidden', !tableSelected);
  });
});

document.querySelector('#copy-data').addEventListener('click', async (event) => {
  const button = event.currentTarget;
  const original = button.textContent;
  try {
    await navigator.clipboard.writeText('Romeo and Juliet\nRomeo: scenes 1, 2, 4, 5, 6, 8, 9, 11, 12\nJuliet: scenes 1, 3, 4, 5, 7, 8, 10, 11, 12');
    button.textContent = '✓ COPIED';
  } catch {
    button.textContent = 'COPY UNAVAILABLE';
  }
  setTimeout(() => { button.textContent = original; }, 1800);
});

document.querySelector('#download-data').addEventListener('click', () => {
  const csv = 'Character,Scene 01,Scene 02,Scene 03,Scene 04,Scene 05\nRomeo,1,1,0,1,1\nJuliet,1,0,1,1,1\nMercutio,1,1,1,0,1';
  const link = document.createElement('a');
  link.href = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
  link.download = 'throughline-romeo-and-juliet.csv';
  link.click();
  URL.revokeObjectURL(link.href);
});
