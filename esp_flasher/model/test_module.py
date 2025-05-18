class TestModule:
    def __init__(
        self, regex, timeout_seconds, test_enabled=False, test_board_xth_occurrence=0
    ):
        self.regex = regex
        self.timeout_seconds = timeout_seconds
        self.is_testing = False
        self.successful_flash_count = 0
        self.test_enabled = test_enabled
        self.test_board_xth_occurrence = test_board_xth_occurrence

    def increment_flash_count(self):
        self.successful_flash_count += 1

    def should_run_test(self):
        return (
            self.test_enabled
            and self.test_board_xth_occurrence > 0
            and (self.successful_flash_count % self.test_board_xth_occurrence == 0)
        )
