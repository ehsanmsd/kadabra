import kadabra
import datetime

from mock import MagicMock, mock, call

NOW = datetime.datetime.utcnow()

class MockDatetime(datetime.datetime):
    "A fake replacement for date that can be mocked for testing."
    def __new__(cls, *args, **kwargs):
        return datetime.datetime.__new__(date, *args, **kwargs)

    @classmethod
    def utcnow(cls):
        return NOW

def test_ctor():
    channel = MagicMock()
    publisher = MagicMock()
    logger = MagicMock()
    frequency_seconds = MagicMock()
    threshold_seconds = MagicMock()
    query_limit = MagicMock()
    num_threads = MagicMock()

    nanny = kadabra.agent.Nanny(channel, publisher, logger, frequency_seconds,
            threshold_seconds, query_limit, num_threads)

    assert nanny.channel == channel
    assert nanny.publisher == publisher
    assert nanny.logger == logger
    assert nanny.frequency_seconds == frequency_seconds
    assert nanny.threshold_seconds == threshold_seconds
    assert nanny.query_limit == query_limit
    assert nanny.num_threads == num_threads

@mock.patch('kadabra.agent.NannyThread')
@mock.patch('kadabra.agent.Timer')
def test_start(mock_timer, mock_nanny_thread):
    channel = MagicMock()
    publisher = MagicMock()
    logger = MagicMock()
    frequency_seconds = MagicMock()
    threshold_seconds = MagicMock()
    query_limit = MagicMock()
    num_threads = 3
    mock_timer.start = MagicMock()

    thread_one = MagicMock()
    thread_one.start = MagicMock()
    thread_two = MagicMock()
    thread_two.start = MagicMock()
    thread_three = MagicMock()
    thread_three.start = MagicMock()

    nanny_threads = [thread_one, thread_two, thread_three]
    mock_nanny_thread.side_effect = nanny_threads

    nanny = kadabra.agent.Nanny(channel, publisher, logger, frequency_seconds,
            threshold_seconds, query_limit, num_threads)
    nanny.start()

    mock_nanny_thread.assert_has_calls(
            [call(channel, publisher, nanny.queue, logger) for x in
                nanny_threads])
    for i in range(len(nanny_threads)):
        expected_name = "KadabraNannyThread-%s" % str(i)
        assert nanny.threads[i].name == expected_name
        nanny_threads[i].start.assert_called_with()

@mock.patch('kadabra.agent.datetime.datetime', MockDatetime)
@mock.patch('kadabra.agent.Timer')
def test_run_nanny(mock_timer):
    metrics_one = MagicMock()
    metrics_one.serialized_at = NOW - datetime.timedelta(seconds=30)
    metrics = [metrics_one]

    channel = MagicMock()
    channel.in_progress = MagicMock(return_value=metrics)
    publisher = MagicMock()
    logger = MagicMock()
    frequency_seconds = MagicMock()
    threshold_seconds = 25
    query_limit = MagicMock()
    num_threads = MagicMock()
    mock_timer.start = MagicMock()

    timer = mock_timer.return_value

    nanny = kadabra.agent.Nanny(channel, publisher, logger, frequency_seconds,
            threshold_seconds, query_limit, num_threads)
    nanny.queue = MagicMock()
    nanny.queue.put = MagicMock()
    nanny.run_nanny()

    channel.in_progress.assert_called_with(query_limit)
    nanny.queue.put.assert_called_with(metrics_one)
    mock_timer.assert_called_with(frequency_seconds, nanny.run_nanny)
    assert timer.name == "KadabraNanny"
    timer.start.assert_called_with()

@mock.patch('kadabra.agent.Timer')
def test_run_nanny_missing_serialized_at(mock_timer):
    metrics_one = MagicMock()
    metrics_one.serialized_at = None
    metrics = [metrics_one]

    channel = MagicMock()
    channel.in_progress = MagicMock(return_value=metrics)
    publisher = MagicMock()
    logger = MagicMock()
    frequency_seconds = MagicMock()
    threshold_seconds = MagicMock()
    query_limit = MagicMock()
    num_threads = MagicMock()
    mock_timer.start = MagicMock()

    timer = mock_timer.return_value

    nanny = kadabra.agent.Nanny(channel, publisher, logger, frequency_seconds,
            threshold_seconds, query_limit, num_threads)
    nanny.queue = MagicMock()
    nanny.queue.put = MagicMock()
    nanny.run_nanny()

    channel.in_progress.assert_called_with(query_limit)
    nanny.queue.put.assert_called_with(metrics_one)
    mock_timer.assert_called_with(frequency_seconds, nanny.run_nanny)
    assert timer.name == "KadabraNanny"
    timer.start.assert_called_with()

@mock.patch('kadabra.agent.Timer')
def test_run_nanny_exception(mock_timer):
    channel = MagicMock()
    channel.in_progress = MagicMock()
    channel.in_progress.side_effect = Exception()
    publisher = MagicMock()
    logger = MagicMock()
    frequency_seconds = MagicMock()
    threshold_seconds = MagicMock()
    query_limit = MagicMock()
    num_threads = MagicMock()
    mock_timer.start = MagicMock()

    timer = mock_timer.return_value

    nanny = kadabra.agent.Nanny(channel, publisher, logger, frequency_seconds,
            threshold_seconds, query_limit, num_threads)
    nanny.queue = MagicMock()
    nanny.queue.put = MagicMock()
    nanny.run_nanny()

    channel.in_progress.assert_called_with(query_limit)
    nanny.queue.put.assert_has_calls([])
    mock_timer.assert_called_with(frequency_seconds, nanny.run_nanny)
    assert timer.name == "KadabraNanny"
    timer.start.assert_called_with()
