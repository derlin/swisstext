function rm(url_match) {
    var query = {
        'crawl_history.0': {'$exists': false},
        url: {$regex: url_match}
    };
    var cnt = db.urls.find(query).count();
    print('Removing', cnt, 'using regex', url_match);
    db.urls.remove(query);
    return cnt;
}

var cnt = 0;

// zscfans
var zsc_host = 'forum\\.zscfans\\.ch';
cnt += rm(zsc_host + '/posting.php');
cnt += rm(zsc_host + '/memberlist.php');
var zsc_cnt = cnt;
print('Removed', zsc_cnt, 'from zscfans');

// celica
var celica_host = 'www\\.celica-t23\\.ch';
cnt += rm(celica_host + '.*' + 'attachment.php');
cnt += rm(celica_host + '.*' + 'report.php');
cnt += rm(celica_host + '.*' + 'formmail.php');
cnt += rm(celica_host + '.*' + 'addreply.php');
cnt += rm(celica_host + '.*' + 'action=add');
print('Removed', cnt - zsc_cnt, 'from celica');

print();
print('Total:', cnt);