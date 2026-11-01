// Fill the shared delete confirmation modal with the record chosen by the user.
// Each delete button provides data-delete-url, data-item-name and optionally data-warning.
(function () {
    const modal = document.getElementById('confirmDeleteModal');
    if (!modal) {
        return;
    }

    modal.addEventListener('show.bs.modal', function (event) {
        const button = event.relatedTarget;
        const warning = modal.querySelector('[data-role="warning"]');

        modal.querySelector('form').setAttribute('action', button.dataset.deleteUrl);
        // textContent (not innerHTML) keeps user-entered names from being treated as HTML.
        modal.querySelector('[data-role="item-name"]').textContent = button.dataset.itemName;
        warning.textContent = button.dataset.warning || '';
        warning.classList.toggle('d-none', !button.dataset.warning);
    });
})();
