import json
import pytest
from tools.files import list_files
import paths


def test_sorted_non_recursive(tmp_path, monkeypatch):
    monkeypatch.setattr(paths, 'WORKSPACE_DIR', tmp_path)
    (tmp_path/'b').mkdir()
    (tmp_path/'b/nested.txt').write_text('fake')
    (tmp_path/'a.txt').write_text('fake')
    assert json.loads(list_files.invoke({'path':'.'})) == {
        'ok':True, 'path':'.', 'entries':[
            {'name':'a.txt','path':'a.txt','type':'file'},
            {'name':'b','path':'b','type':'directory'}]}
    assert json.loads(list_files.invoke({'path':'b'}))['entries'][0]['path']=='b/nested.txt'


@pytest.mark.parametrize('path,code', [('data.txt','NOT_A_DIRECTORY'),('missing','DIRECTORY_NOT_FOUND'),('../escape','PATH_OUTSIDE_WORKSPACE'),('/tmp/example','PATH_OUTSIDE_WORKSPACE'),('','INVALID_PATH')])
def test_errors(tmp_path, monkeypatch, path, code):
    monkeypatch.setattr(paths, 'WORKSPACE_DIR', tmp_path)
    (tmp_path/'data.txt').write_text('fake')
    result=json.loads(list_files.invoke({'path':path}))
    assert not result['ok'] and result['error']['code']==code


def test_symlinks(tmp_path, monkeypatch):
    root=tmp_path/'workspace';root.mkdir()
    outside=tmp_path/'fake-outside';outside.mkdir()
    (outside/'dummy.txt').write_text('synthetic fixture')
    monkeypatch.setattr(paths,'WORKSPACE_DIR',root)
    (root/'escape').symlink_to(outside, target_is_directory=True)
    for path in ['escape','.']:
        result=json.loads(list_files.invoke({'path':path}))
        assert result['error']['code']=='PATH_OUTSIDE_WORKSPACE'
    (root/'escape').unlink()
    (root/'inside').mkdir()
    (root/'alias').symlink_to(root/'inside',target_is_directory=True)
    assert json.loads(list_files.invoke({'path':'alias'}))['ok']


def test_empty_and_rename(tmp_path, monkeypatch):
    monkeypatch.setattr(paths,'WORKSPACE_DIR',tmp_path)
    assert json.loads(list_files.invoke({'path':'.'}))['entries']==[]
    (tmp_path/'old.md').write_text('fake')
    (tmp_path/'old.md').rename(tmp_path/'renamed.md')
    assert json.loads(list_files.invoke({'path':'.'}))['entries'][0]['name']=='renamed.md'
