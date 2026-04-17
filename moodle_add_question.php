<?php
define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->libdir . '/questionlib.php');

if ($argc < 6) {
    echo json_encode(array('success' => false, 'error' => 'Usage: php moodle_add_question.php <quizid> <qtype> <name> <questiontext> <answers_json> [<correct_index>]'));
    exit(1);
}

$quizid = intval($argv[1]);
$qtype = $argv[2]; // multichoice or truefalse
$name = $argv[3];
$questiontext = $argv[4];
$answers_b64 = $argv[5];
$correct_index = isset($argv[6]) ? intval($argv[6]) : 0;

try {
    $answers_json = base64_decode($answers_b64);
    $quiz = $DB->get_record('quiz', array('id' => $quizid), '*', MUST_EXIST);
    $cm = get_coursemodule_from_instance('quiz', $quizid, $quiz->course);
    $context = context_module::instance($cm->id);
    $coursecontext = context_course::instance($quiz->course);

    // Find or create default question category for course context
    $category = $DB->get_record_sql("
        SELECT qc.* 
        FROM {question_categories} qc
        WHERE qc.contextid = :contextid
        ORDER BY qc.id ASC
        LIMIT 1
    ", array('contextid' => $coursecontext->id));

    if (!$category) {
        $catname = 'Default for ' . $coursecontext->get_context_name();
        $category = new stdClass();
        $category->name = $catname;
        $category->contextid = $coursecontext->id;
        $category->info = '';
        $category->infoformat = FORMAT_HTML;
        $category->parent = 0;
        $category->sortorder = 999;
        $category->stamp = make_unique_id_code();
        $category->id = $DB->insert_record('question_categories', $category);
    }

    // Create question bank entry
    $entry = new stdClass();
    $entry->questioncategoryid = $category->id;
    $entry->idnumber = null;
    $entry->ownerid = 2; // admin
    $entry->id = $DB->insert_record('question_bank_entries', $entry);

    // Create question
    $question = new stdClass();
    $question->parent = 0;
    $question->name = substr($name, 0, 255);
    $question->questiontext = $questiontext;
    $question->questiontextformat = FORMAT_HTML;
    $question->generalfeedback = '';
    $question->generalfeedbackformat = FORMAT_HTML;
    $question->defaultmark = 1.0000000;
    $question->penalty = 0.3333333;
    $question->qtype = $qtype;
    $question->length = 1;
    $question->stamp = make_unique_id_code();
    $question->timecreated = time();
    $question->timemodified = time();
    $question->createdby = 2;
    $question->modifiedby = 2;
    $question->id = $DB->insert_record('question', $question);

    // Create version
    $version = new stdClass();
    $version->questionbankentryid = $entry->id;
    $version->version = 1;
    $version->questionid = $question->id;
    $version->status = 'ready';
    $version->id = $DB->insert_record('question_versions', $version);

    // Process answers
    $answers = json_decode($answers_json);
    if (!is_array($answers)) {
        throw new Exception('Invalid answers JSON');
    }

    foreach ($answers as $idx => $ans) {
        $answer = new stdClass();
        $answer->question = $question->id;
        $answer->answer = $ans->text;
        $answer->answerformat = FORMAT_HTML;
        $answer->fraction = floatval($ans->fraction);
        $answer->feedback = '';
        $answer->feedbackformat = FORMAT_HTML;
        $DB->insert_record('question_answers', $answer);
    }

    // Add qtype-specific options
    if ($qtype === 'multichoice') {
        $mc = new stdClass();
        $mc->questionid = $question->id;
        $mc->layout = 0;
        $mc->single = 1;
        $mc->shuffleanswers = 1;
        $mc->correctfeedback = '';
        $mc->correctfeedbackformat = FORMAT_HTML;
        $mc->partiallycorrectfeedback = '';
        $mc->partiallycorrectfeedbackformat = FORMAT_HTML;
        $mc->incorrectfeedback = '';
        $mc->incorrectfeedbackformat = FORMAT_HTML;
        $mc->answernumbering = 'abc';
        $mc->shownumcorrect = 1;
        $mc->showstandardinstruction = 1;
        $DB->insert_record('qtype_multichoice_options', $mc);
    } elseif ($qtype === 'truefalse') {
        $tf = new stdClass();
        $tf->questionid = $question->id;
        $tf->trueanswer = 0;
        $tf->falseanswer = 0;
        $tf->correctfeedback = '';
        $tf->correctfeedbackformat = FORMAT_HTML;
        $tf->partiallycorrectfeedback = '';
        $tf->partiallycorrectfeedbackformat = FORMAT_HTML;
        $tf->incorrectfeedback = '';
        $tf->incorrectfeedbackformat = FORMAT_HTML;
        // Need to update trueanswer/falseanswer after we know answer ids
        // But for now, default to 0 (Moodle handles this on edit)
        $DB->insert_record('question_truefalse', $tf);
    }

    // Add to quiz slot
    $slotnum = $DB->count_records('quiz_slots', array('quizid' => $quizid)) + 1;
    $quizslot = new stdClass();
    $quizslot->slot = $slotnum;
    $quizslot->quizid = $quizid;
    $quizslot->page = $slotnum;
    $quizslot->displaynumber = null;
    $quizslot->requireprevious = 0;
    $quizslot->maxmark = 1.0;
    $quizslot->id = $DB->insert_record('quiz_slots', $quizslot);

    // Link question to slot
    $ref = new stdClass();
    $ref->usingcontextid = $context->id;
    $ref->component = 'mod_quiz';
    $ref->questionarea = 'slot';
    $ref->itemid = $quizslot->id;
    $ref->questionbankentryid = $entry->id;
    $ref->version = 1;
    $DB->insert_record('question_references', $ref);

    // Update quiz sumgrades
    $quiz->sumgrades += 1.0;
    $DB->update_record('quiz', $quiz);

    echo json_encode(array('success' => true, 'question_id' => $question->id, 'slot' => $slotnum));
} catch (Exception $e) {
    echo json_encode(array('success' => false, 'error' => $e->getMessage()));
    exit(1);
}
