#!/bin/ruby

Dir.chdir "_site"

require "aws-sdk"
require "digest"
require "zlib"
require "mime-types"

BASEURL = ENV["BASEURL"]
SITE_PREFIX = ENV["SITE_PREFIX"]
BUCKET = ENV["BUCKET"]
CACHE_CONTROL = ENV["CACHE_CONTROL"]

S3 = Aws::S3::Client.new(
  access_key_id: ENV["AWS_ACCESS_KEY_ID"],
  secret_access_key: ENV["AWS_SECRET_ACCESS_KEY"],
  region: ENV["AWS_DEFAULT_REGION"],
)

DOTFILE_REGEX = /(\/|^)\..*/
GZIP_REGEX = /\.html$|\.css$|\.js$|\.json$|\.svg$/
REDIRECT_REGEX = /(\/|^)index.html/

##
# Code for classes that can be uploaded to S3
#
class SiteObject
  attr_reader :filename, :md5

  def initialize(filename, md5)
    @filename = filename
    @md5 = md5
  end

  def delete_from_s3
    start_time = Time.now
    print "Deleting: #{s3_key}... "
    S3.delete_object(
      bucket: BUCKET,
      key: s3_key,
    )
    puts "Done (#{Time.now - start_time}s)"
  end

  def s3_key
    "#{SITE_PREFIX}/#{filename}"
  end
end

##
# A file produced during a site build
#
class SiteFile < SiteObject
  attr_reader :filename, :md5

  def initialize(filename)
    @filename = filename
    compress
    @md5 = Digest::MD5.file(filename).hexdigest
  end

  def compressable?
    filename.match(GZIP_REGEX)
  end

  def compress
    if compressable?
      contents = File.read(filename)
      Zlib::GzipWriter.open(filename) do |gz|
        # Spoof the modification time so that MD5 hashes match next time
        gz.mtime = Time.parse("March 19, 2014").to_i
        gz.write contents
      end
    end
  end

  def content_type
    if mime_type = MIME::Types.type_for(filename).first
      mime_type.content_type
    end
  end

  def content_encoding
    if compressable?
      "gzip"
    end
  end

  def upload_to_s3
    start_time = Time.now
    print "Uploading: #{s3_key}... "
    S3.put_object(
      body: File.open(filename),
      bucket: BUCKET,
      cache_control: CACHE_CONTROL,
      content_encoding: content_encoding,
      content_type: content_type,
      server_side_encryption: "AES256",
      key: s3_key,
    )
    puts "Done (#{Time.now - start_time}s)"
  end
end

##
# A redirect, typically from `/path/to/page => /path/to/page/`
#
class SiteRedirect < SiteObject
  attr_reader :filename, :md5

  def initialize(filename)
    @filename = filename
    @md5 = Digest::MD5.hexdigest(destination)
  end

  def destination
    if filename == ""
      "/"
    else
      "#{BASEURL}/#{filename}/"
    end
  end

  def upload_to_s3
    start_time = Time.now
    print "Uploading: #{s3_key}... "
    S3.put_object(
      body: destination,
      bucket: BUCKET,
      server_side_encryption: "AES256",
      key: s3_key,
      website_redirect_location: destination,
    )
    puts "Done (#{Time.now - start_time}s)"
  end

  def s3_key
    if filename == ""
      "#{SITE_PREFIX}"
    else
      "#{SITE_PREFIX}/#{filename}"
    end
  end
end

##
# Collect a list of all of the files in the current directory
#
local_files = Dir["**/*"].reject do |filename|
  # Remove directories and dotfiles
  File.directory?(filename) || filename.match(DOTFILE_REGEX)
end.map do |filename|
  SiteFile.new(filename)
end

##
# Create a list of redirects from the local files
#
local_redirects = local_files.find_all do |file|
  file.filename.match(REDIRECT_REGEX)
end.map do |file|
  redirect_filename = file.filename.gsub(REDIRECT_REGEX, "")
  SiteRedirect.new(redirect_filename)
end

##
# Use the local files and redirects to create a list of local objects
#
local_objects = local_files + local_redirects

##
# Download remote files from AWS.
# Use them to create an array of site objects
#
results_truncated = true
continuation_token = nil
remote_objects = []
while results_truncated do
  s3_response = S3.list_objects_v2(
    prefix: SITE_PREFIX,
    bucket: BUCKET,
    continuation_token: continuation_token,
    max_keys: 1000,
  )

  s3_response.contents.each do |response_object|
    filename = response_object.key.gsub(/^#{SITE_PREFIX}\/?/, "")
    md5 = response_object.etag().gsub("\"", "")
    remote_objects.push(SiteObject.new(filename, md5))
  end

  results_truncated = s3_response.is_truncated
  if s3_response.is_truncated
    continuation_token = s3_response.next_continuation_token
  end
end

##
# Find all local objects not on S3
#
new_objects = local_objects.find_all do |local_object|
  !remote_objects.any? { |remote_object| remote_object.filename == local_object.filename }
end

##
# Find all local objects that have been modified from their S3 counterpart
#
modified_objects = local_objects.find_all do |local_object|
  remote_objects.any? { |remote_object| remote_object.filename == local_object.filename && remote_object.md5 != local_object.md5 }
end

##
# Find all S3 objects not present locally
#
deleted_objects = remote_objects.find_all do |remote_object|
  !local_objects.any? { |local_object| local_object.filename == remote_object.filename }
end

puts "Preparing to upload"
puts "New: #{new_objects.length}"
puts "Modified: #{modified_objects.length}"
puts "Deleted: #{deleted_objects.length}"

##
# Upload files that need uploading
#
(new_objects + modified_objects).each do |object|
  object.upload_to_s3
end

##
# Delete files that need deleting
#
deleted_objects.each do |object|
  object.delete_from_s3
end
