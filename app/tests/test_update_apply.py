"""The process that finishes an update after the app has gone.

Windows will not let a running program replace its own files, so the app hands
off to this and exits. Everything here is about the handover being survivable:
it waits for the app to actually go, it refuses rather than half-finishing, and
every way it can fail ends with a message naming the Desktop icon, because the
previous version is still installed and that icon still starts it.

Real folders on this Mac, with RRF_INSTALL_HOME and RRF_DESKTOP pointed into a
temporary directory. What cannot be tested here is Windows itself: a real
console window, a real .lnk, and CREATE_NEW_CONSOLE. Those are Windows
acceptance items and are named as such rather than asserted.
"""
import sys
from pathlib import Path

import pytest

APP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(APP / "server"))
sys.path.insert(0, str(APP))

import install_windows as installer  # noqa: E402
import packaging  # noqa: E402
import startup  # noqa: E402
import update_apply  # noqa: E402

from test_installing_and_updating import make_package  # noqa: E402


@pytest.fixture
def place(tmp_path, monkeypatch):
    home = tmp_path / "LocalAppData" / "Roy R. Fisher"
    desktop = tmp_path / "Desktop"
    desktop.mkdir(parents=True)
    monkeypatch.setenv("RRF_INSTALL_HOME", str(home))
    monkeypatch.setenv("RRF_DESKTOP", str(desktop))
    monkeypatch.setattr(installer.subprocess, "run",
                        lambda *a, **k: (_ for _ in ()).throw(OSError("no powershell")))
    return tmp_path, home, desktop


class Clock:
    """A clock a test can state instead of racing."""

    def __init__(self):
        self.at = 0.0
        self.slept = []

    def now(self):
        return self.at

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.at += seconds


def lines(collected):
    return "\n".join(collected)


def once_installed(home, version):
    """`something_running` as it behaves during an update that works.

    Nothing answers while the old app is closing and the copying is going on,
    and the new version answers once it is there. Real enough for the two waits
    either side of the install, and it does not need a web server.
    """
    def answering(_home):
        return version if (Path(home) / version).is_dir() else ""
    return answering


def never_answers(_home):
    """The 0.6.5 case: it installs, it is started, and it never comes up."""
    return ""


# --- waiting for the app to go ---------------------------------------------
def test_it_waits_while_a_version_is_still_answering(place, monkeypatch):
    _, home, _ = place
    answers = ["0.5.3", "0.5.3", "0.5.3", ""]
    monkeypatch.setattr(installer, "something_running",
                        lambda _h: answers.pop(0))
    clock = Clock()
    assert update_apply.wait_for_the_app_to_close(
        home, sleep=clock.sleep, now=clock.now) == ""
    assert len(clock.slept) == 3, "it stopped waiting before the app had gone"


def test_it_gives_up_after_the_bound_and_names_what_is_still_up(place, monkeypatch):
    _, home, _ = place
    monkeypatch.setattr(installer, "something_running", lambda _h: "0.5.3")
    clock = Clock()
    still = update_apply.wait_for_the_app_to_close(
        home, seconds=5, sleep=clock.sleep, now=clock.now)
    assert still == "0.5.3"


def test_it_waits_on_the_same_condition_the_install_refuses_on(place):
    """Not a proxy for it. Anything else would mean the rule the installer
    enforces and the rule this obeys were two readings of one line."""
    _, home, _ = place
    source = Path(update_apply.__file__).read_text()
    assert "installer.something_running" in source


# --- the app is still up ----------------------------------------------------
def test_it_refuses_plainly_when_the_app_never_closes(place, tmp_path, monkeypatch):
    _, home, _ = place
    monkeypatch.setattr(installer, "something_running", lambda _h: "0.5.3")
    package = make_package(tmp_path / "unzipped", "0.5.4")
    said = []
    clock = Clock()
    code = update_apply.apply(home=home, source=package, out=said.append,
                              sleep=clock.sleep, now=clock.now)
    assert code == 1
    assert "0.5.3 is still running" in lines(said)
    assert "Desktop" in lines(said)
    assert not home.exists(), "it copied something after refusing"


# --- the ordinary case ------------------------------------------------------
def test_it_installs_once_nothing_is_answering(place, tmp_path, monkeypatch):
    _, home, desktop = place
    monkeypatch.setattr(installer, "something_running", once_installed(home, "0.5.4"))
    package = make_package(tmp_path / "unzipped", "0.5.4")
    started = []
    said = []
    code = update_apply.apply(home=home, source=package, out=said.append,
                              spawn=lambda cmd, **kw: started.append(cmd))
    assert code == 0
    assert (home / "0.5.4" / installer.LAUNCHER_NAME).is_file()
    assert "Updated to version 0.5.4" in lines(said)
    assert desktop.exists()


def test_it_says_the_new_version_is_open_only_once_it_has_answered(place, tmp_path,
                                                                   monkeypatch):
    """Not when it was started. Started and running are two different things,
    and 0.6.5 was the difference."""
    _, home, _ = place
    monkeypatch.setattr(installer, "something_running", once_installed(home, "0.5.4"))
    said = []
    code = update_apply.apply(home=home, source=make_package(tmp_path / "u", "0.5.4"),
                              out=said.append, spawn=lambda cmd, **kw: None)
    assert code == 0
    assert "0.5.4 is open" in lines(said)


def test_it_opens_the_version_it_just_installed(place, tmp_path, monkeypatch):
    _, home, _ = place
    monkeypatch.setattr(installer, "something_running", once_installed(home, "0.5.4"))
    package = make_package(tmp_path / "unzipped", "0.5.4")
    started = []
    update_apply.apply(home=home, source=package, out=lambda _s: None,
                       spawn=lambda cmd, **kw: started.append(cmd))
    assert started, "nothing was started after the install"
    assert str(home / "0.5.4" / installer.LAUNCHER_NAME) in started[0]


def test_the_previous_version_is_left_where_it_was(place, tmp_path, monkeypatch):
    """The whole rollback mechanism is that the old folder is still there."""
    _, home, _ = place
    installer.install(make_package(tmp_path / "old", "0.5.3"))
    monkeypatch.setattr(installer, "something_running", once_installed(home, "0.5.4"))
    package = make_package(tmp_path / "new", "0.5.4")
    update_apply.apply(home=home, source=package, out=lambda _s: None,
                       spawn=lambda cmd, **kw: None)
    assert (home / "0.5.3" / installer.LAUNCHER_NAME).is_file()
    assert (home / "0.5.4" / installer.LAUNCHER_NAME).is_file()
    assert (home / installer.ROLLBACK_NAME).is_file()


def test_the_rollback_file_points_at_the_version_he_had(place, tmp_path, monkeypatch):
    _, home, _ = place
    installer.install(make_package(tmp_path / "old", "0.5.3"))
    monkeypatch.setattr(installer, "something_running", once_installed(home, "0.5.4"))
    update_apply.apply(home=home, source=make_package(tmp_path / "new", "0.5.4"),
                       out=lambda _s: None, spawn=lambda cmd, **kw: None)
    assert "0.5.3" in (home / installer.ROLLBACK_NAME).read_text()


# --- a version that installs and then will not start ------------------------
# All of this exists because 0.6.5 did exactly that on 2026-09-03. It installed
# without a complaint, the update said it had worked, and the app could not
# start. Nothing anywhere noticed.
def test_a_version_that_never_answers_is_a_failed_update(place, tmp_path,
                                                         monkeypatch):
    _, home, _ = place
    installer.install(make_package(tmp_path / "old", "0.5.3"))
    monkeypatch.setattr(installer, "something_running", never_answers)
    clock = Clock()
    said = []
    code = update_apply.apply(home=home, source=make_package(tmp_path / "new", "0.5.4"),
                              out=said.append, spawn=lambda cmd, **kw: None,
                              sleep=clock.sleep, now=clock.now)
    assert code == 1, "it called a version that will not start a good update"
    assert "did not start" in lines(said)


def test_it_waits_the_whole_bound_before_calling_it_a_failure(place, tmp_path,
                                                              monkeypatch):
    """A slow machine is not a broken version. Sending Mark back a version
    because his laptop took its time would be a fault of its own."""
    _, home, _ = place
    monkeypatch.setattr(installer, "something_running", never_answers)
    clock = Clock()
    update_apply.apply(home=home, source=make_package(tmp_path / "new", "0.5.4"),
                       out=lambda _s: None, spawn=lambda cmd, **kw: None,
                       sleep=clock.sleep, now=clock.now)
    assert sum(clock.slept) >= update_apply.NEW_VERSION_SECONDS - update_apply.POLL_SECONDS


def test_something_else_answering_does_not_count_as_this_version_starting(place,
                                                                          tmp_path,
                                                                          monkeypatch):
    """The old version coming back up answers too, and that is not this one
    starting."""
    _, home, _ = place
    installer.install(make_package(tmp_path / "old", "0.5.3"))
    # Nothing answers until 0.5.4 is on disk, because the install refuses on
    # this same question. Then the old version is what answers, not the new one.
    monkeypatch.setattr(installer, "something_running",
                        lambda _h: "0.5.3" if (home / "0.5.4").is_dir() else "")
    clock = Clock()
    said = []
    code = update_apply.apply(home=home, source=make_package(tmp_path / "new", "0.5.4"),
                              out=said.append, spawn=lambda cmd, **kw: None,
                              sleep=clock.sleep, now=clock.now)
    assert code == 1
    assert "did not start" in lines(said)


def test_the_way_back_goes_on_the_desktop_when_a_version_will_not_start(place,
                                                                        tmp_path,
                                                                        monkeypatch):
    """It has always been in %LOCALAPPDATA%, which he will never open. This is
    the one moment it is worth something, so this is where it appears."""
    _, home, desktop = place
    installer.install(make_package(tmp_path / "old", "0.5.3"))
    monkeypatch.setattr(installer, "something_running", never_answers)
    clock = Clock()
    said = []
    update_apply.apply(home=home, source=make_package(tmp_path / "new", "0.5.4"),
                       out=said.append, spawn=lambda cmd, **kw: None,
                       sleep=clock.sleep, now=clock.now)
    icon = desktop / installer.WAY_BACK_NAME
    assert icon.is_file(), "he was told to go back with nothing to click"
    assert installer.WAY_BACK_NAME in lines(said), "the icon was not named"
    assert "0.5.3" in lines(said), "it did not say which version he goes back to"


def test_the_desktop_way_back_runs_the_rollback_script_in_the_home_folder(place,
                                                                          tmp_path):
    """One way back, in one place, reached from two. A second copy of the
    logic would be a second thing to get wrong."""
    _, home, desktop = place
    installer.install(make_package(tmp_path / "old", "0.5.3"))
    installer.install(make_package(tmp_path / "new", "0.5.4"))
    written = installer.put_way_back_on_desktop(home, "0.5.3")
    assert written
    body = Path(written).read_text()
    assert str(home) in body
    assert installer.ROLLBACK_NAME in body
    assert "0.5.3" in body


def test_nothing_is_put_on_the_desktop_when_there_is_nothing_to_go_back_to(place,
                                                                           tmp_path):
    _, home, desktop = place
    assert installer.put_way_back_on_desktop(home, "") == ""
    assert not (desktop / installer.WAY_BACK_NAME).exists()


def test_the_way_back_comes_off_the_desktop_once_a_version_answers(place, tmp_path,
                                                                   monkeypatch):
    """Otherwise a bad update leaves an icon offering for ever to undo a
    version that works, which is Spenser's two-icons complaint again."""
    _, home, desktop = place
    installer.install(make_package(tmp_path / "old", "0.5.3"))
    (desktop / installer.WAY_BACK_NAME).write_text("left over", encoding="utf-8")
    monkeypatch.setattr(installer, "something_running", once_installed(home, "0.5.4"))
    update_apply.apply(home=home, source=make_package(tmp_path / "new", "0.5.4"),
                       out=lambda _s: None, spawn=lambda cmd, **kw: None)
    assert not (desktop / installer.WAY_BACK_NAME).exists()


def test_showing_the_way_back_never_raises(place, tmp_path, monkeypatch):
    """It is called on the failure path. A failure path that can itself fail
    is not a failure path."""
    _, home, _ = place

    def no_desktop():
        raise OSError("this machine has no Desktop")

    monkeypatch.setattr(installer, "desktop_folder", no_desktop)
    assert installer.put_way_back_on_desktop(home, "0.5.3") == ""
    installer.take_way_back_off_desktop()


def test_the_failure_names_the_rollback_script_when_no_icon_can_be_written(place,
                                                                           tmp_path,
                                                                           monkeypatch):
    """No Desktop is not no way back. It falls back to naming the path."""
    _, home, _ = place
    installer.install(make_package(tmp_path / "old", "0.5.3"))
    monkeypatch.setattr(installer, "something_running", never_answers)
    monkeypatch.setattr(installer, "put_way_back_on_desktop", lambda _h, _p: "")
    clock = Clock()
    said = []
    update_apply.apply(home=home, source=make_package(tmp_path / "new", "0.5.4"),
                       out=said.append, spawn=lambda cmd, **kw: None,
                       sleep=clock.sleep, now=clock.now)
    assert installer.ROLLBACK_NAME in lines(said)


def test_a_first_install_that_will_not_start_says_there_is_no_way_back(place,
                                                                       tmp_path,
                                                                       monkeypatch):
    """Honest rather than helpful. Offering a way back that is not there would
    be worse than saying so."""
    _, home, desktop = place
    monkeypatch.setattr(installer, "something_running", never_answers)
    clock = Clock()
    said = []
    code = update_apply.apply(home=home, source=make_package(tmp_path / "new", "0.5.4"),
                              out=said.append, spawn=lambda cmd, **kw: None,
                              sleep=clock.sleep, now=clock.now)
    assert code == 1
    assert "nothing to go back to" in lines(said)
    assert not (desktop / installer.WAY_BACK_NAME).exists()


# --- when the install itself goes wrong -------------------------------------
def test_a_refused_install_says_the_previous_version_still_works(place, tmp_path,
                                                                 monkeypatch):
    _, home, _ = place

    def refuse(_source=None):
        raise installer.InstallRefused("This computer would not let it be written.")

    monkeypatch.setattr(installer, "install", refuse)
    said = []
    code = update_apply.apply(home=home, source=tmp_path, out=said.append)
    assert code == 1
    assert "would not let it be written" in lines(said)
    assert update_apply.STILL_WORKS in lines(said)


def test_anything_at_all_going_wrong_still_reads_as_a_sentence(place, tmp_path,
                                                               monkeypatch):
    """This process is the last thing standing between Mark and a closed app.
    A traceback is not something he can act on."""
    _, home, _ = place

    def explode(_source=None):
        raise RuntimeError("something nobody predicted")

    monkeypatch.setattr(installer, "install", explode)
    said = []
    code = update_apply.apply(home=home, source=tmp_path, out=said.append)
    assert code == 1
    assert "did not finish" in lines(said)
    assert "something nobody predicted" in lines(said)
    assert update_apply.STILL_WORKS in lines(said)


def test_failing_to_open_the_new_version_does_not_undo_the_update(place, tmp_path):
    """The update worked. The icon on his Desktop already points at it."""
    _, home, _ = place
    package = make_package(tmp_path / "unzipped", "0.5.4")

    def cannot_start(*_a, **_k):
        raise OSError("no console here")

    said = []
    code = update_apply.apply(home=home, source=package, out=said.append,
                              spawn=cannot_start)
    assert code == 0
    assert (home / "0.5.4" / installer.LAUNCHER_NAME).is_file()
    assert "does not undo the update" in lines(said)
    assert "Desktop" in lines(said)


# --- the window, and the folder it stands in --------------------------------
def test_the_window_is_held_open_on_failure_and_never_raises():
    def no_stdin(_prompt):
        raise EOFError("no console")

    update_apply.hold_the_window(read=no_stdin)


def test_it_never_deletes_the_folder_it_is_standing_in():
    """The scratch folder is cleared at the start of the next attempt instead.
    Asserted on the source, because the failure would be a process deleting
    itself part way through."""
    source = Path(update_apply.__file__).read_text()
    assert "rmtree" not in source
    assert "clear_scratch" not in source


def test_it_ships_beside_the_installer_it_calls():
    """It runs out of the new package. If packaging ever stopped carrying it,
    an update would install a version that could not itself be updated."""
    assert (APP / "update_apply.py").is_file()
    assert (APP / "install_windows.py").is_file()
