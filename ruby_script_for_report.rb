require 'report_builder'

    # Ex 1:
    ReportBuilder.configure do |config|
      config.input_path = 'templates/json_report.json'
      config.report_path = 'templates/my_test_report'
      config.report_types = [:retry, :html]
      config.report_title = 'Reonomy Results'
      config.additional_info = {browser: 'Chrome', environment: 'production'}
    end

    ReportBuilder.build_report