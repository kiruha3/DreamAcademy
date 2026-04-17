<?php
define('CLI_SCRIPT', true);
require('/var/www/html/config.php');
require_once($CFG->dirroot . '/mod/quiz/locallib.php');

if ($argc < 4) {
    echo json_encode(array('success' => false, 'error' => 'Usage: php moodle_process_attempt.php <attemptid> <data_json> <finishattempt>'));
    exit(1);
}

$attemptid = intval($argv[1]);
$data_json = base64_decode($argv[2]);
$finishattempt = boolval($argv[3]);

try {
    $attempt = $DB->get_record('quiz_attempts', array('id' => $attemptid), '*', MUST_EXIST);
    $USER = $DB->get_record('user', array('id' => $attempt->userid), '*', MUST_EXIST);

    $data = json_decode($data_json, true);
    if (!is_array($data)) {
        throw new Exception('Invalid data JSON');
    }

    $result = mod_quiz_external::process_attempt($attemptid, $data, $finishattempt, false);
    echo json_encode(array('success' => true, 'result' => $result));
} catch (Exception $e) {
    echo json_encode(array('success' => false, 'error' => $e->getMessage()));
    exit(1);
}
