from top_containers.cli import main


def test_top_containers_with_modify_data_success(runner, working_directory):
    result = runner.invoke(
        main,
        [
            "--as_instance",
            "prod",
            "--directory",
            working_directory,
            "--metadata_csv",
            "test_metadata.csv",
            "--repository_id",
            "0",
            "--modify_data",
        ],
        "y",
    )
    assert result.exit_code == 0


def test_top_containers_without_modify_data_success(runner, working_directory):
    result = runner.invoke(
        main,
        [
            "--as_instance",
            "prod",
            "--directory",
            working_directory,
            "--metadata_csv",
            "test_metadata.csv",
            "--repository_id",
            "0",
        ],
    )
    assert result.exit_code == 0


def test_top_containers_wrong_user_input_causes_exit(caplog, runner, working_directory):
    result = runner.invoke(
        main,
        [
            "--as_instance",
            "prod",
            "--directory",
            working_directory,
            "--metadata_csv",
            "test_metadata.csv",
            "--repository_id",
            "0",
            "--modify_data",
        ],
        "x",
    )
    assert result.exit_code == 0
    assert "Halting process based on user input 'x' which is not 'y'" in caplog.text
