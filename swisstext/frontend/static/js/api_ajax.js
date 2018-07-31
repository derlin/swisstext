function ajax_undelete_sentence(id) {
    return $.ajax({url: `/api/sentences/${id}/restore`, method: "GET", contentType: 'application/json'});
}

function ajax_delete_sentence(id) {
    return $.ajax({url: `/api/sentences/${id}`, method: "DELETE", contentType: 'application/json'});
}