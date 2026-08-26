package io.github.macmacs.af.data;

import io.github.macmacs.af.util.AfLocationInfo;

public interface AfDataSource {

	void update(AfLocationInfo afLocationInfo, long currentUtcTime) throws AfDataUpdateException;

}
