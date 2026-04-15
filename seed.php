<?php
define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->dirroot.'/course/lib.php');
require_once($CFG->dirroot.'/mod/forum/lib.php');
require_once($CFG->dirroot.'/mod/quiz/lib.php');
require_once($CFG->dirroot.'/mod/page/lib.php');
require_once($CFG->dirroot.'/mod/url/lib.php');
require_once($CFG->dirroot.'/mod/assign/lib.php');
require_once($CFG->dirroot.'/mod/label/lib.php');
require_once($CFG->dirroot.'/lib/resourcelib.php');

$courseid = isset($argv[1]) ? intval($argv[1]) : 2;
$course = get_course($courseid);

// Clean existing modules in course (except section 0 news forum if it exists)
$cms = $DB->get_records('course_modules', ['course' => $course->id]);
foreach ($cms as $cm) {
    if ($cm->section == 0) {
        $sec = $DB->get_record('course_sections', ['id' => $cm->section]);
        if ($sec && $sec->section == 0) {
            // keep default news forum in section 0; delete others
            $mod = $DB->get_record('modules', ['id' => $cm->module]);
            if ($mod && $mod->name == 'forum') {
                $inst = $DB->get_record('forum', ['id' => $cm->instance]);
                if ($inst && $inst->type == 'news') {
                    continue;
                }
            }
        }
    }
    course_delete_module($cm->id);
}
// Reset sequences
$DB->set_field('course_sections', 'sequence', '', ['course' => $course->id]);
rebuild_course_cache($course->id, true);
$modinfo = get_fast_modinfo($course);
$sections = $modinfo->get_section_info_all();

function ensure_section($course, $sectionnum, $name) {
    global $DB;
    $sec = $DB->get_record('course_sections', ['course' => $course->id, 'section' => $sectionnum]);
    if (!$sec) {
        $sec = new stdClass();
        $sec->course = $course->id;
        $sec->section = $sectionnum;
        $sec->name = $name;
        $sec->summary = '';
        $sec->summaryformat = FORMAT_HTML;
        $sec->sequence = '';
        $sec->visible = 1;
        $sec->id = $DB->insert_record('course_sections', $sec);
    } else if (empty($sec->name)) {
        $sec->name = $name;
        $DB->update_record('course_sections', $sec);
    }
    return $sec;
}

function add_mod($course, $modname, $sectionnum, $data) {
    global $DB, $CFG;
    $module = $DB->get_record('modules', ['name' => $modname], '*', MUST_EXIST);
    $data->module = $module->id;
    $data->modulename = $modname;
    $data->course = $course->id;
    $data->section = $sectionnum;
    $data->visible = 1;
    $data->visibleoncoursepage = 1;
    $cmid = add_course_module($data);
    if (!$cmid) {
        echo "Failed to add $modname: " . ($data->name ?? 'unknown') . "\n";
        return null;
    }
    course_add_cm_to_section($course->id, $cmid, $sectionnum);
    echo "Added $modname: " . ($data->name ?? 'unknown') . " (cmid=$cmid)\n";
    return $cmid;
}

$sec0 = ensure_section($course, 0, 'Общие сведения');
$sec1 = ensure_section($course, 1, 'Теория');
$sec2 = ensure_section($course, 2, 'Практика');

// Section 0: Forum news
$forum = new stdClass();
$forum->name = 'Новости курса';
$forum->intro = 'Объявления и новости';
$forum->introformat = FORMAT_HTML;
$forum->type = 'news';
$forum->duedate = 0;
$forum->cutoffdate = 0;
add_mod($course, 'forum', 0, $forum);

// Section 1: Page + URL + Label
$page = new stdClass();
$page->name = 'Введение в DreamDocs';
$page->intro = 'Краткое введение';
$page->introformat = FORMAT_HTML;
$page->content = '<p>DreamDocs помогает автоматизировать документооборот. В этом модуле мы рассмотрим основные возможности.</p>';
$page->contentformat = FORMAT_HTML;
add_mod($course, 'page', 1, $page);

$url = new stdClass();
$url->name = 'Официальный сайт DreamDocs';
$url->intro = 'Полезная ссылка';
$url->introformat = FORMAT_HTML;
$url->externalurl = 'https://dreamdocs.ru';
$url->display = RESOURCELIB_DISPLAY_OPEN;
add_mod($course, 'url', 1, $url);

$label = new stdClass();
$label->name = 'Важно';
$label->intro = '<div class="alert alert-info">Изучите теорию перед прохождением теста.</div>';
$label->introformat = FORMAT_HTML;
add_mod($course, 'label', 1, $label);

// Section 2: Quiz + Assignment + Forum
$quiz = new stdClass();
$quiz->name = 'Проверка знаний';
$quiz->intro = 'Пройдите тест из 10 вопросов';
$quiz->introformat = FORMAT_HTML;
$quiz->grade = 10;
$quiz->sumgrades = 10;
$quiz->timeopen = 0;
$quiz->timeclose = 0;
add_mod($course, 'quiz', 2, $quiz);

$assign = new stdClass();
$assign->name = 'Практическое задание';
$assign->intro = 'Загрузите готовый документ по шаблону';
$assign->introformat = FORMAT_HTML;
$assign->duedate = time() + 7*24*3600;
$assign->grade = 100;
add_mod($course, 'assign', 2, $assign);

$forum2 = new stdClass();
$forum2->name = 'Обсуждения';
$forum2->intro = 'Задавайте вопросы и делитесь опытом';
$forum2->introformat = FORMAT_HTML;
$forum2->type = 'general';
add_mod($course, 'forum', 2, $forum2);

rebuild_course_cache($course->id, true);
echo "Done seeding course $courseid\n";
