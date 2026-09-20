const sourceForm = document.querySelector('#source-form');
const sourceFeedback = document.querySelector('#source-feedback');
const urlInput = document.querySelector('#play-url');
const uploadInput = document.querySelector('#pdf-upload');
const clearButton = document.querySelector('.clear-button');
const plotView = document.querySelector('#plot-view');
const tableView = document.querySelector('#table-view');

sourceForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const source = urlInput.value.trim();
  sourceFeedback.textContent = source ? 'Source queued for analysis. Showing sample result below.' : 'Add a URL before analyzing.';
  sourceFeedback.style.color = source ? 'var(--green)' : 'var(--red)';
  if (source) document.querySelector('#results-heading').scrollIntoView({ behavior: 'smooth', block: 'start' });
});

clearButton.addEventListener('click', () => {
  urlInput.value = '';
  urlInput.focus();
  sourceFeedback.textContent = '';
});

uploadInput.addEventListener('change', () => {
  const file = uploadInput.files[0];
  if (!file) return;
  sourceFeedback.textContent = `${file.name} ready for analysis. Showing sample result below.`;
  sourceFeedback.style.color = 'var(--green)';
});

document.querySelectorAll('.view-option').forEach((button) => {
  button.addEventListener('click', () => {
    document.querySelectorAll('.view-option').forEach((option) => option.classList.remove('active'));
    button.classList.add('active');
    const showTable = button.dataset.view === 'table';
    plotView.classList.toggle('hidden', showTable);
    tableView.classList.toggle('hidden', !showTable);
  });
});

document.querySelector('#copy-data').addEventListener('click', async (event) => {
  const button = event.currentTarget;
  const original = button.innerHTML;
  const text = 'Romeo and Juliet\nRomeo: scenes 1, 2, 4, 5, 6, 8, 9, 11, 12\nJuliet: scenes 1, 3, 4, 5, 7, 8, 10, 11, 12';
  try {
    await navigator.clipboard.writeText(text);
    button.innerHTML = '<span class="button-icon">✓</span> Copied';
  } catch {
    button.textContent = 'Select table to copy';
  }
  setTimeout(() => { button.innerHTML = original; }, 1800);
});

document.querySelector('#download-data').addEventListener('click', () => {
  const csv = 'Character,Scene 01,Scene 02,Scene 03,Scene 04,Scene 05\nRomeo,1,1,0,1,1\nJuliet,1,0,1,1,1\nMercutio,1,1,1,0,1';
  const blob = new Blob([csv], { type: 'text/csv' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'throughline-romeo-and-juliet.csv';
  link.click();
  URL.revokeObjectURL(link.href);
});
