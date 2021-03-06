% Generated by roxygen2: do not edit by hand
% Please edit documentation in R/cdh_utils.R
\name{latestSnapshotsOnly}
\alias{latestSnapshotsOnly}
\title{Subset the provided datamart data to just the latest snapshot per model.}
\usage{
latestSnapshotsOnly(dt)
}
\arguments{
\item{dt}{The \code{data.table} with the datamart data.}
}
\value{
A \code{data.table} with just the latest snapshots per model.
}
\description{
If there is just one snapshot, nothing will change. It works for both
model and predictor tables. If there is no snapshottime field, it will
not do anything.
}
\examples{
latestSnapshotsOnly(admdatamart_binning)
}
